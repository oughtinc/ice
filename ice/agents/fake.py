import random

from faker import Faker

from ice.agents.base import Agent

random.seed(0)
Faker.seed(0)


class FakeAgent(Agent):
    def __init__(self):
        self.fake = Faker()

    async def relevance(self, *, question, context, verbose=False, default=None):
        return random.random()

    async def answer(
        self,
        *,
        prompt: str,
        multiline: bool = True,
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
        default: str | None = None,
        verbose: bool = False,
    ) -> tuple[dict[str, float], str | None]:
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
