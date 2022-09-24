# type: ignore
import asyncio

from pathlib import Path
from typing import Type

import streamlit as st

from ice import execution_context
from ice.metrics.gold_standards import retrieve_gold_standards_df
from ice.paper import get_paper_paths
from ice.paper import Paper
from ice.recipe import Recipe
from ice.recipes import get_recipe_classes


@st.cache
def get_question_short_names():
    gold_df = retrieve_gold_standards_df()
    question_short_names = gold_df["question_short_name"].unique()
    return question_short_names


def select_question(default_value: str | None = None):
    question_short_names = get_question_short_names()
    extra_args = {}
    if default_value is not None:
        extra_args["index"] = list(question_short_names).index(default_value)
    question_short_name = st.selectbox(
        "Select question",
        question_short_names,
        **extra_args,
    )
    return question_short_name


def select_recipe_class(*, default_value: str | None = None) -> Type[Recipe]:
    recipe_classes = get_recipe_classes()
    recipe_names = [r.__name__ for r in recipe_classes]
    extra_params = {}
    if default_value is not None:
        extra_params["index"] = recipe_names.index(default_value)
    recipe_name = st.sidebar.selectbox("Select a recipe", recipe_names, **extra_params)
    recipe_class = [r for r in recipe_classes if r.__name__ == recipe_name][0]
    return recipe_class


def select_paper(*, default_value: str | None = None):
    paper_paths = get_paper_paths()
    paper_path_strings = [str(f) for f in paper_paths]
    extra_params = {}
    if default_value is not None:
        default_value_index = None
        resolved_default_path = Path(default_value).resolve()
        for i, path in enumerate(paper_paths):
            if path.resolve() == resolved_default_path:
                default_value_index = i
                break
        if default_value_index is not None:
            extra_params["index"] = default_value_index
    paper_path_str = st.sidebar.selectbox(
        "Select a paper", paper_path_strings, **extra_params
    )
    paper = Paper.load(Path(paper_path_str))
    return paper


def run_recipe(recipe: Recipe, paper: Paper):
    execution_context.new_context(document_id=paper.document_id, task="n/a")
    with st.spinner(f"Running recipe '{recipe}'"):
        result = asyncio.run(recipe.execute(question="n/a", paper=paper))
    return result
