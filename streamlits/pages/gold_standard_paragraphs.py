# type: ignore
import asyncio

import streamlit as st

from stqdm import stqdm

from ice.metrics.gold_paragraphs import get_gold_paragraph_df
from ice.paper import Paragraph
from ice.recipe import Recipe
from ice.streamlit_utils import select_question
from ice.streamlit_utils import select_recipe_class


@st.cache
def _cached_gold_paragraph_df(question: str):
    return get_gold_paragraph_df(question)


def cached_gold_paragraph_df(question: str):
    df, id_to_paragraph = _cached_gold_paragraph_df(question)
    return df.copy(), id_to_paragraph


@st.cache
def run_recipe_on_paragraph(recipe: Recipe, paragraph: Paragraph, experiment: str):

    paragraph_result = asyncio.run(
        recipe.analyze_paragraph(
            paragraph=paragraph,
            experiment=experiment,
        )
    )

    # FIXME: Below is specific to the placebo recipe.

    placebo_prob = paragraph_result["used_placebo"]["placebo_prob"]
    no_placebo_prob = paragraph_result["used_placebo"]["no_placebo_prob"]

    if placebo_prob > 0.5 and no_placebo_prob <= 0.5:
        paragraph_classification = "Placebo"
    elif placebo_prob <= 0.5 and no_placebo_prob > 0.5:
        paragraph_classification = "No placebo"
    elif placebo_prob > 0.5 and no_placebo_prob > 0.5:
        paragraph_classification = "Unclear"
    else:
        paragraph_classification = "Not mentioned"

    paragraph_data = dict(
        {"paragraph_classification": paragraph_classification},
        **paragraph_result["used_placebo"]["components"],
    )
    return paragraph_data


def main():

    st.set_page_config(layout="wide")

    with st.sidebar:
        recipe_class = select_recipe_class(
            default_value="Placebo via paragraph-wise dialogs"
        )
        question = select_question(default_value="placebo")

    if not hasattr(recipe_class, "analyze_paragraph"):
        st.write("Recipe doesn't have an analyze_paragraph method")
        return

    paragraph_df, id_to_paragraph = cached_gold_paragraph_df(question)

    # Run machine recipe on gold paragraphs
    recipe = recipe_class(mode="machine")
    for row_index, row in stqdm(list(paragraph_df.iterrows())):
        paragraph = id_to_paragraph[row["paragraph_id"]]
        experiment = row["experiment"]
        paragraph_result = run_recipe_on_paragraph(recipe, paragraph, experiment)
        result_column_names = paragraph_result.keys()
        paragraph_df.loc[row_index, result_column_names] = paragraph_result

    st.dataframe(paragraph_df, height=1000)


if __name__ == "__main__":
    main()
