from collections.abc import Sequence

from structlog.stdlib import get_logger


log = get_logger()


CONSENSUS_PREFIX = "Below are some answers to the question '{question}'"
CLUSTER_DIRECTIONS = """Cluster these answers by how they answer the question '{question}'. Write your answer in the form "Cluster N) [Answer]":

Cluster 1)"""

FINAL_DIRECTIONS = """Based on these clusters, write a single, detailed answer based on a consensus of the proposed answers, that is most likely to be correct.

Detailed, consensus answer:"""


def candidates(
    answers: Sequence[str], prefix: str = "Answer", separator: str = "\n"
) -> str:
    return separator.join(
        (f"{prefix} {idx}) {answer.strip()}" for idx, answer in enumerate(answers, 1))
    )


def build_cluster_prompt(question: str, answers: Sequence[str]) -> str:
    prefix = CONSENSUS_PREFIX.format(question=question)
    return "\n\n".join(
        (prefix, candidates(answers), CLUSTER_DIRECTIONS.format(question=question))
    )


def build_final_prompt(question: str, answers: Sequence[str], clusters: str) -> str:
    cluster_prompt = build_cluster_prompt(question, answers)
    return "\n\n".join((cluster_prompt + clusters.rstrip(), FINAL_DIRECTIONS))
