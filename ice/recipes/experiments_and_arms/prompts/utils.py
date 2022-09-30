from typing import Sequence
from typing_extensions import assert_never
from ice.formatter.transform.value import ValueTransform
from ice.formatter.multi import StopSentinel, stop
from ice.recipes.experiments_and_arms.types import ReasoningStage, PassageWithReasoning
from collections import Counter


def start_last_example(
    helpfulness: str | None,
    reasoning: str | None,
    pre_final: str | None = None,
    pre_helpful: str | None = None,
    pre_answer: str | None = None,
) -> dict[str, ValueTransform[Sequence[str]] | str | StopSentinel]:
    assert (
        not helpfulness or reasoning
    ), "Final reasoning required alongside helpfulness"

    state: ReasoningStage = (
        "reasoning"
        if not reasoning
        else "helpfulness"
        if not helpfulness
        else "answer"
    )

    match state:
        case "reasoning":
            return {"reasoning": stop(pre_final or "")}
        case "helpfulness":
            assert reasoning
            return {
                "reasoning": reasoning,
                "helpfulness": stop(pre_helpful or ""),
            }
        case "answer":
            assert reasoning and helpfulness
            return {
                "reasoning": reasoning,
                "helpfulness": helpfulness,
                "answer": stop(pre_answer or ""),
            }
        case _:
            assert_never(state)

def get_part(response: str, pre_part: str, post_part: str) -> str:
    split = response.split(pre_part)
    remaining = split[1] if len(split) > 1 else split[0]
    return remaining.split(post_part)[0].strip()


async def plurality_greedy(
    samples: Sequence[PassageWithReasoning[int]],
) -> PassageWithReasoning[int]:
    most_common = Counter(
        [s.final_answer for s in samples if s.final_answer is not None]
    ).most_common(1)[0][0]
    for sample in samples:
        if sample.final_answer == most_common:
            return sample
    raise RuntimeError("Unreachable")
