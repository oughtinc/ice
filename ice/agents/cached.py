from typing import Optional

from ice.agents.base import Agent
from ice.agents.base import Stop
from ice.settings import CACHE_DIR
from ice.sqlite_shelf import SQLiteShelf


def get_cache_key(fn_name: str, input: str):
    return f"{fn_name}___{input}"


class CachedAgent(Agent):
    cache: SQLiteShelf

    def __init__(self, base_agent: Agent, cache_name: str = "cached_agent"):
        cache_file = (CACHE_DIR / "cached_agent.sqlite").as_posix()
        self.cache = SQLiteShelf(cache_file, cache_name)
        self.base_agent = base_agent

    async def complete(
        self,
        *,
        prompt,
        stop: Stop = None,
        verbose=False,
        default="",
        max_tokens: int = 256,
    ) -> str:
        key = get_cache_key("answer", prompt)
        if key in self.cache:
            return self.cache[key]
        answer = await self.base_agent.complete(
            prompt=prompt,
            stop=stop,
            verbose=verbose,
            default=default,
            max_tokens=max_tokens,
        )
        self.cache[key] = answer
        return answer

    async def predict(self, *, context, default="", verbose=False) -> dict[str, float]:
        key = get_cache_key("predict", context)
        if key in self.cache:
            return self.cache[key]
        prediction = await self.base_agent.predict(
            context=context, default=default, verbose=verbose
        )
        self.cache[key] = prediction
        return prediction

    async def classify(
        self,
        *,
        prompt: str,
        choices: tuple[str, ...],
        default: Optional[str] = None,
        verbose: bool = False,
    ) -> tuple[dict[str, float], Optional[str]]:
        key = get_cache_key("classify", prompt)
        if key in self.cache:
            return self.cache[key]
        classification = await self.base_agent.classify(
            prompt=prompt, choices=choices, verbose=verbose
        )
        self.cache[key] = classification
        return classification

    async def relevance(
        self, *, question: str, context: str, verbose=False, default=None
    ) -> float:
        key = get_cache_key("relevance", f"{question}___{context}")
        if key in self.cache:
            return self.cache[key]
        relevance = await self.base_agent.relevance(
            context=context, question=question, verbose=verbose, default=default
        )
        self.cache[key] = relevance
        return relevance
