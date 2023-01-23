from dataclasses import dataclass
from typing import Optional
from typing import Protocol


@dataclass
class Example:
    question: Optional[str]
    texts: list[str]
    compressed: list[str]


class Compress(Protocol):
    async def __call__(
        self, question: Optional[str], texts: list[str], examples: list[Example]
    ) -> list[str]:
        pass
