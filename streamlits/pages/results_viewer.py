# type: ignore
import asyncio

import streamlit as st

from ice.streamlit_utils import run_recipe
from ice.streamlit_utils import select_paper
from ice.streamlit_utils import select_recipe_class


def main():
    recipe_class = select_recipe_class(
        default_value="Placebo via paragraph-wise dialogs"
    )
    paper = select_paper(default_value="papers/keenan-2018.pdf")
    recipe = recipe_class(mode="machine")
    run_recipe(recipe, paper)
    evaluation_report = asyncio.run(recipe.evaluation_report())
    st.write(evaluation_report.classification_summaries)
    for evaluation_result in evaluation_report.results:
        st.write(evaluation_result.dict())


if __name__ == "__main__":
    main()
