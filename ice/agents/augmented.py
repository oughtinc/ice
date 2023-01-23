from typing import Optional

from ice.agents.base import Agent
from ice.agents.base import Stop
from ice.environment import env
from ice.utils import max_by_value
from ice.utils import quoted


class AugmentedAgent(Agent):
    def __init__(self, human: Agent, machine: Agent):
        self.human = human
        self.machine = machine

    async def relevance(
        self, *, question, context, verbose=False, default=None
    ) -> float:
        machine_resp = await self.machine.relevance(
            question=question, context=context, verbose=verbose
        )
        human_resp = await self.human.relevance(
            question=question, context=context, verbose=verbose, default=machine_resp
        )
        return human_resp

    async def complete(
        self,
        *,
        prompt: str,
        stop: Stop = None,
        verbose: bool = False,
        default: str = "",
        max_tokens: int = 256,
    ):
        machine_resp = await self.machine.complete(
            prompt=prompt,
            stop=stop,
            verbose=verbose,
            default=default,
            max_tokens=max_tokens,
        )
        return await self.human.complete(
            prompt=prompt,
            stop=stop,
            verbose=verbose,
            default=machine_resp,
            max_tokens=max_tokens,
        )

    async def predict(self, *, context, default="", verbose=False) -> dict[str, float]:
        machine_resp: dict[str, float] = await self.machine.predict(
            context=context, verbose=verbose
        )
        # Extract most likely response from machine_resp and use it as default for human.
        most_likely_token = max(machine_resp, key=lambda k: machine_resp[k])
        human_resp = await self.human.predict(
            context=context, default=most_likely_token, verbose=verbose
        )
        return human_resp

    async def classify(
        self,
        *,
        prompt: str,
        choices: tuple[str, ...],
        default: Optional[str] = None,
        verbose: bool = False,
    ) -> tuple[dict[str, float], Optional[str]]:
        (machine_probs, explanation) = await self.machine.classify(
            prompt=prompt,
            choices=choices,
            default=default,
            verbose=verbose,
        )
        machine_choice, _ = max_by_value(machine_probs)
        if explanation is not None:
            # TODO: Should present this to the human in a way that does
            #       not circumvent agent abstraction
            env().print(
                f"""
#### classify

Machine choice probs:

{machine_probs}

Explanation for machine probs:

{quoted(explanation)}""",
                format_markdown=True,
            )
        return await self.human.classify(
            prompt=prompt,
            choices=choices,
            default=machine_choice,
            verbose=verbose,
        )
