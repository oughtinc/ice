from typing import Optional

from ice.agents.base import Agent
from ice.agents.base import Stop
from ice.environment import env


class HumanAgent(Agent):
    async def complete(
        self,
        *,
        prompt: str,
        stop: Stop = None,
        verbose: bool = False,
        default: str = "",
        max_tokens: int = 256,
    ) -> str:
        verbose  # ignored for HumanAgent
        multiline = (
            False if stop is None or "\n" in stop else True
        )  # TODO: better way to detect multiline
        completion = await env().answer(prompt, default=default, multiline=multiline)
        return completion

    async def relevance(
        self, *, question, context, verbose=False, default=None
    ) -> float:
        verbose  # ignored for HumanAgent
        score = await env().score(question, context, default=default)
        return score

    async def predict(
        self, *, context: str, default="", verbose=False
    ) -> dict[str, float]:
        verbose  # ignored for HumanAgent
        completion = await env().answer(context, default=default, multiline=False)
        return {completion: 1.0}

    async def classify(
        self,
        *,
        prompt: str,
        choices: tuple[str, ...],
        default: Optional[str] = None,
        verbose: bool = False,
    ) -> tuple[dict[str, float], Optional[str]]:
        choice = await env().select(
            prompt=prompt, choices=list(choices), default=default
        )
        return {choice: 1.0}, None
