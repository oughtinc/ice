import pandas as pd

# from ice.recipes.synthesize_ft import synthesize_ft_from_df
# from ice.recipes.synthesize_chain_of_thought import synthesize_chain_of_thought_from_df
from ice.recipes.synthesize_compositional import synthesize_compositional_from_df
# from ice.recipes.synthesize import synthesize_from_df
from ice.recipe import Recipe, recipe
from ice.recipes.run_over_gs import run_over_gs
from ice.utils import order_columns

RECIPE_TO_RUN = synthesize_compositional_from_df
GS_DF = pd.read_csv("data/Paragraph synthesis fine-tuning data - Gold standards.csv")

async def eval_synthesize():
    answers_df = await run_over_gs(RECIPE_TO_RUN, GS_DF)
    answers_df["question"] = answers_df["document_id"]
    merged_df = answers_df.merge(GS_DF, on="question", how="left", suffixes=("_answer", "_gs"))
    merged_df = merged_df.sort_values(["question", "technique"])
    rating_cols_to_add = ["citedness (0-1)", "hallucination (0 = none, 2 = substantive)", "answer_rating", "failure_modes", "notes"]
    for col in rating_cols_to_add:
        merged_df[col] = ""
    merged_df = order_columns(merged_df, [
        "technique",
        "question",
        "answer",
        "papers_cited",
        "synthesis",
    ] + rating_cols_to_add + [
        "citation_1",
        "abstract_1",
        "paper_1_answer",
        "citation_2",
        "abstract_2",
        "paper_2_answer",
        "citation_3",
        "abstract_3",
        "paper_3_answer",
        "citation_4",
        "abstract_4",
        "paper_4_answer"
    ])

    merged_df.to_csv(f"data/{RECIPE_TO_RUN.__name__}_eval.csv", index=False)

    return merged_df

recipe.main(eval_synthesize)


