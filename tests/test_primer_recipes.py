from importlib import import_module
from inspect import signature
from pathlib import Path

import pytest
from faker import Faker

from ice import utils
from ice.paper import Paper
from ice.recipe import FunctionBasedRecipe, recipe
from ice.trace import enable_trace

Faker.seed(0)
fake = Faker()


root_dir = Path(__file__).parent.parent

recipe.all_recipes = []
primer_recipes_dir = root_dir / "ice" / "recipes" / "primer"
for path in primer_recipes_dir.glob("**/*.py"):
    relative_path = path.relative_to(primer_recipes_dir)
    module_name = ".".join(relative_path.parts[:-1] + (relative_path.stem,))
    import_module(f"ice.recipes.primer.{module_name}")

# TODO someday maybe share this with [settings.py]
paper = Paper.load(Path(root_dir / "papers" / "keenan-2018-tiny.txt"))

# TODO someday: find a way to generalize the module-level fixtures to all tests (or at least document it)
# TODO test the actual elicit server :)


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True, scope="module")
async def wq(anyio_backend):
    from ice.work_queue import WorkQueue

    MAX_CONCURRENCY = 1
    wq = WorkQueue(max_concurrency=MAX_CONCURRENCY)
    utils.set_work_queue(wq)
    yield
    await wq.stop()


@pytest.mark.parametrize("main", recipe.all_recipes)
@pytest.mark.anyio
async def test_all_primer_recipes(main: FunctionBasedRecipe):
    kwargs = {}
    for p in signature(main).parameters.values():
        print(f"p={p.annotation}")
        print(f"{Paper=}")
        # print(f"{issubclass(Paper, p.annotation)=}")
        print(f"{issubclass(p.annotation, str)=}")
        print(f"{type(Paper)=}")
        print(f"{issubclass(p.annotation, Paper)=}")
        if p.default is not p.empty:
            value = p.default
        elif issubclass(p.annotation, str):
            value = fake.sentence()
        elif issubclass(p.annotation, Paper):
            value = paper
        else:
            raise ValueError(f"Cannot handle parameter {p}")
        kwargs[p.name] = value
    enable_trace()
    await main(**kwargs)
