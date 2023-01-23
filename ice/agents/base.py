from typing import Optional
from typing import Union

from ice.trace import TracedABC

Stop = Optional[Union[str, list[str]]]


class Agent(TracedABC):
    label: Optional[str] = None

    async def complete(
        self,
        *,
        prompt: str,
        stop: Stop = None,
        verbose: bool = False,
        default: str = "",
        max_tokens: int = 256,
    ) -> str:
        raise NotImplementedError

    async def classify(
        self,
        *,
        prompt: str,
        choices: tuple[str, ...],
        default: Optional[str] = None,
        verbose: bool = False,
    ) -> tuple[dict[str, float], Optional[str]]:
        raise NotImplementedError

    # Methods below may be deprecated in the future:

    async def relevance(
        self,
        *,
        context: str,
        question: str,
        verbose: bool = False,
        default: Optional[float] = None,
    ) -> float:
        raise NotImplementedError

    async def predict(
        self, *, context: str, default: str = "", verbose: bool = False
    ) -> dict[str, float]:
        raise NotImplementedError
