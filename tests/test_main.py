import inspect

from typing import Type

import nest_asyncio
import pytest

from ice.recipe import Recipe
from ice.recipes import get_recipe_classes
from main import main_cli


nest_asyncio.apply()


def do_not_test(recipe: Type[Recipe]) -> bool:
    if hasattr(recipe, "do_not_test"):
        return recipe.do_not_test  # type: ignore
    return False


def takes_paper_arg(recipe_class):
    run_signature = inspect.signature(recipe_class.run)
    return "paper" in run_signature.parameters


# Get recipe classes that take a paper argument in their run method
paper_recipe_classes = [
    recipe_class
    for recipe_class in get_recipe_classes()
    if not do_not_test(recipe_class) and takes_paper_arg(recipe_class)
]

# Get recipe classes that do not take a paper argument in their run method
no_paper_recipe_classes = [
    recipe_class
    for recipe_class in get_recipe_classes()
    if not do_not_test(recipe_class) and not takes_paper_arg(recipe_class)
]


@pytest.mark.parametrize(
    "recipe_name",
    [recipe_class.__name__ for recipe_class in paper_recipe_classes],
)
@pytest.mark.anyio
async def test_paper_recipes(recipe_name: str):
    main_cli(
        mode="test",
        input_files=["./papers/keenan-2018-tiny.txt"],
        recipe_name=recipe_name,
    )


@pytest.mark.parametrize(
    "recipe_name",
    [recipe_class.__name__ for recipe_class in no_paper_recipe_classes],
)
@pytest.mark.anyio
async def test_no_paper_recipes(recipe_name: str):
    main_cli(
        mode="test",
        recipe_name=recipe_name,
    )
