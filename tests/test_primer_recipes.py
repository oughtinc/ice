from importlib import import_module
from inspect import signature
from pathlib import Path

import pytest

from faker import Faker

from ice.paper import Paper
from ice.recipe import FunctionBasedRecipe
from ice.recipe import recipe

Faker.seed(0)
fake = Faker()


root_dir = Path(__file__).parent.parent

primer_recipes_dir = root_dir / "ice" / "recipes" / "primer"
for path in primer_recipes_dir.glob("**/*.py"):
    relative_path = path.relative_to(primer_recipes_dir)
    module_name = ".".join(relative_path.parts[:-1] + (relative_path.stem,))
    import_module(f"ice.recipes.primer.{module_name}")

paper = Paper.load(Path(root_dir / "papers" / "keenan-2018-tiny.txt"))


@pytest.mark.parametrize("main", recipe.all_recipes)
@pytest.mark.anyio
async def test_all_primer_recipes(main: FunctionBasedRecipe):
    kwargs = {}
    for p in signature(main).parameters.values():
        if p.default is not p.empty:
            value = p.default
        elif issubclass(p.annotation, str):
            value = fake.sentence()
        elif issubclass(p.annotation, Paper):
            value = paper
        else:
            raise ValueError(f"Cannot handle parameter {p}")
        kwargs[p.name] = value
    await main(**kwargs)
