import random
from typing import Optional

from faker import Faker

from ice.agents.base import Agent
from ice.agents.base import Stop

random.seed(0)
Faker.seed(0)


class FakeAgent(Agent):
    def __init__(self):
        self.fake = Faker()

    async def relevance(self, *, question, context, verbose=False, default=None):
        return random.random()

    async def complete(
        self,
        *,
        prompt: str,
        stop: Stop = None,
        verbose: bool = False,
        default: str = "",
        max_tokens: int = 256,
    ):
        return self.fake.sentence()

    async def classify(
        self,
        *,
        prompt: str,
        choices: tuple[str, ...],
        default: Optional[str] = None,
        verbose: bool = False,
    ) -> tuple[dict[str, float], Optional[str]]:
        probs = [random.random() for _ in choices]
        total = sum(probs)
        probs = [p / total for p in probs]
        distribution = dict(zip(choices, probs))
        return distribution, None

    async def predict(
        self, *, context: str, default: str = "", verbose: bool = False
    ) -> dict[str, float]:
        if default:
            words = [default]
        else:
            words = []
        words += [self.fake.word() for _ in range(random.randint(1, 5))]
        return {word: random.random() for word in words}
