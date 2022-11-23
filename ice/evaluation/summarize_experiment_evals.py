import ast
import asyncio
from sys import argv

import pandas as pd

from ice.environment import env
from ice.evaluation.evaluate_recipe_result import EvaluatedRecipeResult
from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.evaluation.evaluation_report import EvaluationReport
from ice.evaluation.utils import CSVS_PATH
from ice.evaluation.utils import start_time
from ice.utils import map_async


async def summarize_experiment_evals(results_file: str):
    data_df = pd.read_csv(results_file)
    # data_df["recipe"] = "In-app QA"

    eval_dfs = [
        df for _, df in data_df.groupby(["recipe", "elicit_commit"], dropna=False)
    ]
    dashboard_row_dfs = []
    experiment_evaluations_dfs = []

    for recipe_df in eval_dfs:
        recipe_results_for_evaluation = [
            RecipeResult(
                question_short_name=row.question_short_name,
                document_id=row.document_id,
                answer="" if pd.isna(row.answer) else row.answer,
                experiment=row.experiment,
                excerpts=ast.literal_eval(row.excerpts),
                classifications=[
                    row.get("classification_1"),
                    row.get("classification_2"),
                ],
                answer_rating=None
                if pd.isna(row.get("answer_rating"))
                else int(row.get("answer_rating")),
                elicit_commit=row.get("elicit_commit"),
                failure_modes=None
                if pd.isna(row.get("failure_modes"))
                else row.failure_modes.split(","),
            )
            for _, row in recipe_df.iterrows()
        ]

        evaluation_report = EvaluationReport(
            technique_name=recipe_df["recipe"].iloc[0],
            results=await map_async(
                recipe_results_for_evaluation, EvaluatedRecipeResult.from_recipe_result
            ),
        )

        env().print(
            str(evaluation_report), format_markdown=True, wait_for_confirmation=True
        )

        experiment_evaluations_dfs.append(
            evaluation_report.make_experiments_evaluation_df()
        )
        dashboard_row_dfs.append(evaluation_report.make_dashboard_row_df())

    if len(eval_dfs) > 1:
        dashboard_rows_df = pd.concat(dashboard_row_dfs)
        recipes_str = " ".join(data_df.recipe.unique())
        dashboard_rows_df.to_csv(
            CSVS_PATH / f"dashboard_rows {recipes_str} {start_time}.csv"
        )

        experiment_evaluations_df = pd.concat(experiment_evaluations_dfs)
        experiment_evaluations_df.to_csv(
            CSVS_PATH / f"experiment_evaluations {recipes_str} {start_time}.csv"
        )


if __name__ == "__main__":
    asyncio.run(summarize_experiment_evals(argv[1]))
