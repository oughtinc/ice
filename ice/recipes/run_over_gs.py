import pandas as pd
from ice.recipe import Recipe, recipe
from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.utils import map_async
from ice.evaluation.evaluation_report import EvaluationReport
from ice.evaluation.evaluate_recipe_result import EvaluatedRecipeResult

def make_recipe_result(row: pd.Series) -> RecipeResult:
    return RecipeResult(
        question_short_name=row.question_short_name,
        document_id=row.get("document_id", ""),
        answer="" if pd.isna(row.answer) else row.answer,
        experiment=row.get("experiment", ""),
        excerpts=row.get("excerpts", []),
    )

async def run_recipe_on_row(row: pd.Series, recipe_to_run: Recipe):
    return await recipe_to_run(**row)

async def run_over_gs(recipe_to_run: Recipe, gs_df: pd.DataFrame) -> EvaluationReport:
    gs_df["answer"] = await map_async(
        [row for _, row in gs_df.iterrows()],
        lambda row: run_recipe_on_row(row, recipe_to_run),
        # set this if you're getting OpenAI errors
        # max_concurrency=1
    )
    recipe_results = gs_df.apply(make_recipe_result, axis=1)
    evaluation_report = EvaluationReport(
        technique_name=recipe_to_run.__name__,
        results=await map_async(
            recipe_results, EvaluatedRecipeResult.from_recipe_result
        ),
    )
    return evaluation_report.make_experiments_evaluation_df()