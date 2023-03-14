import abc
import re
import sys
from contextvars import ContextVar
from io import TextIOWrapper
from typing import Any
from typing import cast
from typing import Optional
from typing import TypeVar

import nest_asyncio
import questionary
import rich
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import pretty_repr
from rich.table import Table
from structlog import get_logger

log = get_logger()


class FloatZeroOneValidator(questionary.Validator):
    def validate(self, document):
        ok = re.match(r"^(0(\.\d+)?|1(\.0+)?)$", document.text)
        if not ok:
            raise questionary.ValidationError(
                message="Please enter a number between 0 and 1",
                cursor_position=len(document.text),
            )


class EnvironmentInterface(abc.ABC):
    def spinner(self, msg: str):
        raise NotImplementedError

    def print(
        self,
        msg: Any,
        *,
        format_markdown=False,
        wait_for_confirmation=False,
        file: Optional[str] = None,
    ) -> None:
        raise NotImplementedError

    async def checkboxes(self, prompt: str, choices: list[str]) -> list[str]:
        raise NotImplementedError

    async def answer(self, prompt: str, default: str, multiline: bool = True) -> str:
        raise NotImplementedError

    async def score(
        self, question: str, context: str, default: Optional[float]
    ) -> float:
        # TODO: Make this generic classification instead of implicit single-class search
        raise NotImplementedError

    async def select(
        self, prompt: str, choices: list[str], default: Optional[str] = None
    ) -> str:
        raise NotImplementedError


Environment = TypeVar("Environment", bound=EnvironmentInterface)


class CliEnvironment(EnvironmentInterface):
    def __init__(self):
        try:
            nest_asyncio.apply()  # Needed for questionary to work
        except Exception:
            log.warning("Nest_asyncio failed to apply.")
            pass
        self._console = Console()

    def spinner(self, msg):
        return self._console.status(msg)

    def print(
        self,
        msg: Any,
        *,
        format_markdown: bool = False,
        wait_for_confirmation: bool = False,
        file: Optional[str] = None,
    ):
        if file:
            output = open(file, "a", encoding="utf-8")
        else:
            output = cast(TextIOWrapper, sys.stdout)

        # Create a console object with the appropriate file and width
        console = Console(file=output, width=80 if file else None)

        # Convert the message to a list of rich elements if needed
        if hasattr(msg, "to_rich_elements"):
            msg = msg.to_rich_elements()
        else:
            msg = [msg]

        # Print each element with the console object
        for element in msg:
            if isinstance(element, str):
                if format_markdown:
                    element = Markdown(element)
            elif isinstance(element, Table):
                pass
            else:
                element = pretty_repr(element)
            console.print(
                element, soft_wrap=True, crop=False, no_wrap=True, markup=False
            )

    def _maybe_print_prompt(self, prompt) -> str:
        if "\n" in prompt:
            rich.print(Panel(Markdown(prompt)))
            question = ""
        else:
            question = prompt
        return question

    async def checkboxes(self, prompt: str, choices: list[str]) -> list[str]:
        question = self._maybe_print_prompt(prompt)
        selections = questionary.checkbox(question, choices=choices).ask()
        if selections is None:
            print(prompt)
            raise ValueError("No selections provided")
        return cast(list[str], selections)

    async def answer(self, prompt: str, default: str, multiline: bool = True) -> str:
        question = self._maybe_print_prompt(prompt)
        answer = questionary.text(question, default=default, multiline=multiline).ask()
        if answer is None:
            print(prompt)
            raise ValueError("No answer provided")
        return cast(str, answer)

    async def select(
        self, prompt: str, choices: list[str], default: Optional[str] = None
    ) -> str:
        question = self._maybe_print_prompt(prompt)
        answer = questionary.select(question, choices=choices, default=default).ask()
        if answer is None:
            print(prompt)
            raise ValueError("No answer provided")
        return cast(str, answer)

    async def score(
        self, question: str, context: str, default: Optional[float]
    ) -> float:
        score = questionary.text(
            f"Score the relevance of Context:\n{context}\n\nto Question: {question}",
            default=str(default or ""),
            validate=FloatZeroOneValidator,
        ).ask()
        if score is None:
            print(question)
            raise ValueError("No score provided")
        return float(cast(str, score))


_env = ContextVar("env", default=cast(EnvironmentInterface, CliEnvironment()))


def set_env(env: EnvironmentInterface):
    global _env
    _env.set(env)


def env() -> EnvironmentInterface:
    return _env.get()
