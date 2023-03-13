import shelve
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from ice.agents.base import Agent
from ice.agents.base import Stop


class NotApprovedException(Exception):
    pass


def quoted(s: str):
    return "\n".join(f"> {line}" for line in s.split("\n"))


def is_yes(s: str):
    return s.strip().lower().startswith("y")


class ApprovalAgent(Agent):
    """
    Checks with base agent if action is ok before executing it; if not,
    raises Exception
    """

    def __init__(
        self,
        base_agent: Agent,
        approval_agent: Agent,
        approval_cache_path: Optional[Path] = None,
    ):
        self.base_agent = base_agent
        self.approval_agent = approval_agent
        self.approval_cache_path = approval_cache_path

    @contextmanager
    def approval_cache(self):
        if self.approval_cache_path:
            with shelve.open(self.approval_cache_path.as_posix()) as cache:
                yield cache
        else:
            yield {}

    async def complete(
        self,
        *,
        prompt: str,
        stop: Stop = None,
        verbose: bool = False,
        default: str = "",
        max_tokens: int = 256,
    ):
        completion = await self.base_agent.complete(
            prompt=prompt,
            stop=stop,
            verbose=verbose,
            default=default,
            max_tokens=max_tokens,
        )
        await self._check(prompt=prompt, candidate=completion)
        return completion

    async def relevance(self, *, question, context, verbose=False, default=None):
        score = await self.base_agent.relevance(
            question=question, context=context, verbose=verbose, default=default
        )
        await self._check(
            prompt=f"Score the relevance of the context {context}\n to the question {question}",
            candidate=str(score),
        )
        return score

    async def _check(self, prompt: str, candidate: str):
        approval_prompt = f"""Evaluate whether the following output is correct.

Input:
{quoted(prompt)}

Output:
{quoted(candidate)}

Is this output correct (y/n)?"""

        with self.approval_cache() as cache:
            if approval_prompt in cache:
                assert is_yes(str(cache[approval_prompt]))
                return

        approval_action = await self.approval_agent.complete(prompt=approval_prompt)

        if not is_yes(approval_action):
            raise NotApprovedException

        with self.approval_cache() as cache:
            cache[approval_prompt] = approval_action
