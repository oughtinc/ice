from collections.abc import Sequence
from dataclasses import dataclass

from ice.formatter.transform.value import numbered_list


@dataclass
class Demonstration:
    question: str
    texts: Sequence[str]
    answer: str

    def as_dict(self):
        return dict(
            question=self.question, texts=numbered_list(self.texts), answer=self.answer
        )


@dataclass
class DemonstrationWithReasoning(Demonstration):
    reasoning: str

    def as_dict(self):
        return dict(
            question=self.question,
            texts=numbered_list(self.texts),
            answer=self.answer,
            reasoning=self.reasoning,
        )
