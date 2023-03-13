import importlib.util
import os.path
from typing import Optional
from typing import Type

from ice.environment import env
from ice.recipe import Recipe
from ice.recipes import get_recipe_classes


def is_filename(name: str) -> bool:
    """
    Check if name is a valid filename with a .py extension
    """
    return os.path.isfile(name) and name.endswith(".py")


def load_recipe_class_from_file(filename: str) -> Type[Recipe]:
    # Load the recipe class from the specified file using importlib
    spec = importlib.util.spec_from_file_location("recipe_module", filename)
    if spec is None:
        raise ValueError(f"Could not load recipe from file {filename}")
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if loader is None:
        raise ValueError(f"Could not load recipe from file {filename}")
    loader.exec_module(module)
    # Find the last subclass of Recipe in the module
    recipe_class = None
    for name, obj in vars(module).items():
        try:
            if issubclass(obj, Recipe) and obj is not Recipe:
                recipe_class = obj
        except TypeError:
            # obj is not a class, skip it
            continue
    # Raise an exception if no recipe class is found
    if recipe_class is None:
        raise ValueError(f"No recipe class found in {filename}")
    return recipe_class


def load_recipe_class_by_name(recipe_name: str) -> Type[Recipe]:
    recipe_classes = get_recipe_classes()
    try:
        recipe_class = next(
            r
            for r in recipe_classes
            if r.__name__.lower().startswith(recipe_name.lower())
        )
    except StopIteration:
        raise ValueError(
            f"Recipe '{recipe_name}' not found in {[r.__name__ for r in recipe_classes]}"
        )
    return recipe_class


async def ask_user_for_recipe_class() -> Type[Recipe]:
    recipe_classes = get_recipe_classes()
    recipe_names = [r.__name__ for r in recipe_classes]
    recipe_name = await env().select("Recipe", recipe_names)
    recipe_class = [r for r in recipe_classes if r.__name__ == recipe_name][0]
    return recipe_class


async def select_recipe_class(*, recipe_name: Optional[str] = None) -> Type[Recipe]:
    if recipe_name is not None:
        if is_filename(recipe_name):
            recipe_class = load_recipe_class_from_file(recipe_name)
        else:
            recipe_class = load_recipe_class_by_name(recipe_name)
    else:
        recipe_class = await ask_user_for_recipe_class()
    return recipe_class
