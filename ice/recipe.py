import asyncio
import importlib.util
import sys
from abc import abstractmethod
from collections.abc import Awaitable
from collections.abc import Callable
from functools import wraps
from inspect import iscoroutinefunction
from pathlib import Path
from traceback import print_exc
from typing import cast
from typing import final
from typing import Generic
from typing import no_type_check
from typing import Optional
from typing import TypeVar
from typing import Union

import defopt
import pandas as pd
from merge_args import merge_args
from pydantic_settings import BaseSettings
from structlog.stdlib import get_logger
from typing_extensions import TypeGuard

from ice.agent import Agent
from ice.agent import agent_policy
from ice.environment import env
from ice.evaluation.evaluate_recipe_result import EvaluatedRecipeResult
from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.evaluation.evaluation_report import EvaluationReport
from ice.mode import Mode
from ice.paper import Paper
from ice.trace import enable_trace
from ice.trace import trace
from ice.trace import TracedABC
from ice.utils import map_async

RecipeSettings = TypeVar("RecipeSettings", bound=BaseSettings)

log = get_logger()


def is_list_of_recipe_result(value: object) -> TypeGuard[list[RecipeResult]]:
    return isinstance(value, list) and all(
        isinstance(item, RecipeResult) for item in value
    )


class Recipe(TracedABC, Generic[RecipeSettings]):
    defaults: Callable[["Recipe"], RecipeSettings] = lambda self: cast(
        RecipeSettings, BaseSettings()
    )

    def __init__(
        self, mode: Mode = "machine", settings: Optional[RecipeSettings] = None
    ):
        self.mode = mode
        self.s = settings or self.defaults()  # type: ignore[call-arg,misc]
        self.results: list[RecipeResult] = []

    @classmethod
    def slug(cls) -> str:
        """A unique identifier for this recipe, which does not change when the recipe is updated."""
        return cls.__name__.lower()

    @no_type_check
    @abstractmethod
    async def run(self, **kwargs):
        raise NotImplementedError

    @final
    def maybe_add_to_results(self, results: Union[list[RecipeResult], object]):
        if is_list_of_recipe_result(results):
            self.results.extend(results)

    def to_json(self, results: Union[list[RecipeResult], object]) -> list[dict]:
        """Convert results to objects that can be serialized to JSON."""
        if is_list_of_recipe_result(results):
            return [result.dict() for result in results]
        raise NotImplementedError

    async def evaluation_report(self) -> EvaluationReport:
        return EvaluationReport(
            technique_name=str(self),
            results=await map_async(
                self.results, EvaluatedRecipeResult.from_recipe_result
            ),
        )

    def agent(self, agent_name: Optional[str] = None) -> Agent:
        return agent_policy(mode=self.mode, agent_name=agent_name)

    def max_concurrency(self) -> int:
        return 10 if self.mode == "machine" else 1

    def __str__(self) -> str:
        return self.__class__.__name__


FunctionBasedRecipe = Callable[..., Awaitable]


def function_recipe_from_path(path: str) -> FunctionBasedRecipe:
    # from https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    file_path, _, recipe = path.partition(":")
    module_name = file_path.replace("/", ".").replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return vars(module)[recipe]


class RecipeHelper:
    def __init__(self):
        self._mode: Optional[Mode] = "machine"
        self.all_recipes: list[FunctionBasedRecipe] = []

    def main(self, main: FunctionBasedRecipe):
        if not iscoroutinefunction(main):
            raise TypeError("recipe.main must be given an async function")

        # Trace all globals defined in main's module.
        try:
            g = main.__globals__
        except AttributeError:
            # Perhaps this is a functools.partial
            g = main.func.__globals__  # type: ignore[attr-defined]
        for name, value in g.items():
            if getattr(value, "__module__", None) == main.__module__:
                g[name] = trace(value)

        traced_main = trace(main)
        self.all_recipes.append(traced_main)

        if main.__module__ != "__main__":
            return

        # The frontend shows everything under the first traced root.
        # TODO: Once main.py is gone, change the frontend and get rid of this wrapper.
        @trace
        @wraps(main)
        async def hidden_wrapper(*args, **kwargs):
            try:
                result = await traced_main(*args, **kwargs)
            except NameError:
                print_exc()
                print(
                    "\nReminder: recipe.main should be at the bottom of the file",
                    file=sys.stderr,
                )
                sys.exit(1)

            env().print(result, format_markdown=False)
            return result

        # A traced function cannot be called until the event loop is running.
        @wraps(main)
        async def untraced_wrapper(*args, **kwargs):
            return await hidden_wrapper(*args, **kwargs)

        @merge_args(main)
        def cli(
            *args,
            mode: Mode = "machine",
            trace: bool = True,
            **kwargs,
        ):
            self._mode = mode
            if trace:
                enable_trace()
            asyncio.run(untraced_wrapper(*args, **kwargs))

        defopt.run(
            cli,
            cli_options="all",
            short={},
            parsers={
                Paper: lambda path: Paper.load(Path(path)),
                FunctionBasedRecipe: function_recipe_from_path,
                pd.DataFrame: lambda path: pd.read_csv(path),
            },
        )

    def agent(self, agent_name: Optional[str] = None) -> Agent:
        assert self._mode
        return agent_policy(self._mode, agent_name)


recipe = RecipeHelper()
