import pandas as pd
from ice.recipe import Recipe, recipe
from ice.recipes.synthesize import synthesize_from_df
from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.utils import map_async
from ice.evaluation.evaluation_report import EvaluationReport
from ice.evaluation.evaluate_recipe_result import EvaluatedRecipeResult
from ice.recipes.synthesize_ft import synthesize_ft_from_df
from ice.recipes.synthesize_chain_of_thought import synthesize_chain_of_thought_from_df
from ice.recipes.synthesize_compositional import synthesize_compositional_from_df

GS_FILENAME = "data/Paragraph synthesis fine-tuning data - Gold standards.csv"
recipe_to_run = synthesize_compositional_from_df

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

async def run_over_df():
    gs_df = pd.read_csv(GS_FILENAME)
    gs_df["answer"] = await map_async(
        [row for _, row in gs_df.iterrows()],
        lambda row: run_recipe_on_row(row, recipe_to_run),
        # max_concurrency=1
    )
    recipe_results = gs_df.apply(make_recipe_result, axis=1)
    evaluation_report = EvaluationReport(
        technique_name=recipe_to_run.__name__,
        results=await map_async(
            recipe_results, EvaluatedRecipeResult.from_recipe_result
        ),
    )
    evaluation_report.make_experiments_evaluation_df()

recipe.main(run_over_df)