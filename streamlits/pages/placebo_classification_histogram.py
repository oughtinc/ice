# type: ignore
import pandas as pd
import plotly.express as px
import streamlit as st

from ice.recipes.placebo_dialogs import PlaceboDialogs
from ice.streamlit_utils import run_recipe
from ice.streamlit_utils import select_paper


def main():

    recipe = PlaceboDialogs(mode="machine")

    # Let user select a paper

    paper = select_paper()

    # Run recipe

    recipe_result = run_recipe(recipe, paper)

    # Let user select an experiment

    experiments = list(recipe_result.keys())
    if not experiments:
        st.write("No experiments found")
        return
    experiment = st.selectbox("Select experiment", experiments)

    paragraph_infos = recipe_result[experiment]["paragraph_infos"]

    # Let user select classification component

    component_names = ["open_control", "explicit_placebo", "explicit_no_placebo"]
    component_name = st.selectbox("Select component", component_names)
    component_data = [
        paragraph["used_placebo"]["components"][component_name]
        for paragraph in paragraph_infos
    ]

    keys = list(component_data[0].keys())

    # Let user select Boolean answer key (yes/no)

    key = st.selectbox("Select key", keys)

    component_points = [
        [component_datum[key], i] for (i, component_datum) in enumerate(component_data)
    ]

    points_df = pd.DataFrame(
        component_points, columns=[component_name, "paragraph_index"]
    )

    fig = px.histogram(
        points_df,
        x=component_name,
        marginal="rug",
        hover_data=points_df.columns,
    )
    fig.update_xaxes(range=[0, 1])

    st.plotly_chart(fig)

    # Let user select a paragraph

    paragraph_index = st.number_input(
        "Select paragraph", value=0, min_value=0, max_value=len(paragraph_infos) - 1
    )

    st.markdown(paper.paragraphs[paragraph_index])

    paragraph_info = paragraph_infos[paragraph_index]
    st.write(paragraph_info)


if __name__ == "__main__":
    main()
