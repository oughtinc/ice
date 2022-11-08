from dataclasses import dataclass
from typing import Protocol


@dataclass
class Example:
    question: str | None
    texts: list[str]
    compressed: list[str]


class Compress(Protocol):
    async def __call__(
        self, question: str | None, texts: list[str], examples: list[Example]
    ) -> list[str]:
        pass
