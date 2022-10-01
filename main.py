#! /usr/bin/env python
import asyncio
import json

from pathlib import Path

import defopt

from structlog.stdlib import get_logger

from ice import execution_context
from ice.cli_utils import select_recipe_class
from ice.environment import env
from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.metrics.gold_standards import retrieve_gold_standards_df
from ice.mode import Mode
from ice.paper import Paper
from ice.recipe import is_list_of_recipe_result
from ice.recipe import Recipe
from ice.trace import enable_trace
from ice.trace import trace
from ice.utils import map_async


log = get_logger()


def main_cli(
    *,
    mode: Mode = "machine",
    output_file: str | None = None,
    json_out: str | None = None,
    recipe_name: str | None = None,
    input_files: list[str] | None = None,
    gold_standard_splits: list[str] | None = None,
    question_short_name: str | None = None,
    trace: bool = True,
    args: dict | None = None,
):
    """
    ::
    Run a recipe.
    :param mode Mode:
    :param output_file:  Append output to a file in markdown format instead of stdout.
    :param json_out:  Write recipe-specific JSON output to a file.
    :param recipe_name:  Name of the recipe to run.
    :param input_files:  List of files to run recipe over.
    :param gold_standard_splits: "iterate", "validation", and/or "test"
    """
    if trace:
        enable_trace()

    async def main_wrapper():
        # A traced function cannot be called until the event loop is running.
        return await main(
            mode=mode,
            output_file=output_file,
            json_out=json_out,
            recipe_name=recipe_name,
            input_files=input_files,
            gold_standard_splits=gold_standard_splits,
            question_short_name=question_short_name,
            args=args or {},
        )

    asyncio.run(main_wrapper())


@trace
async def main(
    *,
    mode: Mode,
    output_file: str | None,
    json_out: str | None,
    recipe_name: str | None,
    input_files: list[str] | None,
    gold_standard_splits: list[str] | None,
    question_short_name: str | None,
    args: dict,
):
    # User selects recipe
    recipe = await get_recipe(recipe_name, mode)

    # User selects papers
    papers = await get_papers(input_files, gold_standard_splits, question_short_name)

    if papers:
        print(
            f"Running recipe {recipe} over papers {', '.join(p.document_id for p in papers)}"
        )

    # Run recipe without paper arguments
    if not papers:
        result = await recipe.run(**args)
        env().print(
            result,
            format_markdown=False,
            file=output_file,
        )
        return

    # Run recipe over papers
    results_by_doc = await run_recipe_over_papers(recipe, papers, args)

    # Print results
    results_json = await print_results(recipe, results_by_doc, output_file, json_out)

    # Print evaluation of results
    await evaluate_results(recipe, results_json, output_file)


async def get_recipe(recipe_name: str | None, mode: Mode) -> Recipe:
    """
    Get the recipe instance based on the user input or selection.
    """
    recipe_class = await select_recipe_class(recipe_name=recipe_name)
    return recipe_class(mode)


async def get_papers(
    input_files: list[str] | None,
    gold_standard_splits: list[str] | None,
    question_short_name: str | None,
) -> list[Paper]:
    """
    Get the list of papers based on the user input or selection.
    """
    if (gold_standard_splits is None) != (question_short_name is None):
        raise ValueError(
            "Must specify both gold_standard_splits and question_short_name or neither."
        )

    if input_files:
        paper_files = [Path(i) for i in input_files]
    elif gold_standard_splits:
        gs_df = retrieve_gold_standards_df()
        question_gs_in_splits = gs_df[
            (gs_df.question_short_name == question_short_name)
            & (gs_df.split.isin(gold_standard_splits))
            & (gs_df["Are quotes enough?"] != "No")
        ]
        paper_dir = Path(__file__).parent / "papers/"
        paper_files = [
            f
            for f in paper_dir.iterdir()
            if f.name in question_gs_in_splits.document_id.unique()
        ]
    else:
        paper_files = []

    # If user doesn't specify papers via CLI args, we could prompt them
    # but this makes it harder to run recipes that don't take papers as
    # arguments, so we won't do that here.

    # if input_files is None and gold_standard_splits is None:
    #     paper_names = [f.name for f in paper_files]
    #     selected_paper_names = await env().checkboxes("Papers", paper_names)
    #     paper_files = [f for f in paper_files if f.name in selected_paper_names]

    return [Paper.load(f) for f in paper_files]


async def run_recipe_over_papers(
    recipe: Recipe, papers: list[Paper], args: dict
) -> dict[str, RecipeResult]:
    """
    Run the recipe over the papers and return a map from paper ids to recipe results.
    """

    async def apply_recipe_to_paper(paper: Paper):
        execution_context.new_context(document_id=paper.document_id, task=str(recipe))
        return await recipe.run(paper=paper, **args)

    # Run recipe over papers
    max_concurrency = 5 if recipe.mode == "machine" else 1
    results = await map_async(
        papers,
        apply_recipe_to_paper,
        show_progress_bar=True,
        max_concurrency=max_concurrency,
    )

    return {paper.document_id: result for (paper, result) in zip(papers, results)}


async def print_results(
    recipe: Recipe,
    results_by_doc: dict[str, RecipeResult],
    output_file: str | None,
    json_out: str | None,
) -> list[dict]:
    """
    Print the results to the output file or stdout, and return the JSON representation of the results.
    """
    results_json: list[dict] = []

    for (document_id, final_result) in results_by_doc.items():

        if json_out is not None:
            results_json.extend(recipe.to_json(final_result))

        env().print(
            f"## Final result for {document_id}\n",
            format_markdown=False if output_file else True,
            wait_for_confirmation=False,
            file=output_file,
        )

        if is_list_of_recipe_result(final_result):
            results_to_print = [r.result for r in final_result]
        else:
            results_to_print = [final_result]

        for result_to_print in results_to_print:
            env().print(
                result_to_print,
                format_markdown=False,
                wait_for_confirmation=False,
                file=output_file,
            )

    if json_out is not None:
        with open(json_out, "w") as f:
            json.dump(results_json, f, indent=2)

    return results_json


async def evaluate_results(
    recipe: Recipe, results_json: list[dict], output_file: str | None
):
    """
    Evaluate the results using the recipe's evaluation report and
    dashboard row methods, and print the report to the output file or
    stdout.
    """
    if recipe.results:
        evaluation_report = await recipe.evaluation_report()

        env().print(
            evaluation_report,
            format_markdown=False if output_file else True,
            wait_for_confirmation=True,
            file=output_file,
        )

        evaluation_report.make_dashboard_row_df()
        evaluation_report.make_experiments_evaluation_df()


if __name__ == "__main__":
    defopt.run(main_cli, parsers={dict: json.loads})
