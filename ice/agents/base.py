from ice.trace import TracedABC

Stop = str | list[str] | None


class Agent(TracedABC):
    label: str | None = None

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
        default: str | None = None,
        verbose: bool = False,
    ) -> tuple[dict[str, float], str | None]:
        raise NotImplementedError

    # Methods below may be deprecated in the future:

    async def relevance(
        self,
        *,
        context: str,
        question: str,
        verbose: bool = False,
        default: float | None = None,
    ) -> float:
        raise NotImplementedError

    async def predict(
        self, *, context: str, default: str = "", verbose: bool = False
    ) -> dict[str, float]:
        raise NotImplementedError
