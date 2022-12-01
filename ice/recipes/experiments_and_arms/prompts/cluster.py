from collections.abc import Sequence

from structlog.stdlib import get_logger


log = get_logger()


CLUSTER_PREFIX = "Below are some answers to the question '{question}'"
CLUSTER_DIRECTIONS = """Cluster these answers by how they answer the question '{question}'. Write your answer in the form "Cluster N) [Answer]":

Cluster 1)"""

COUNT_DIRECTIONS = """How many answers are in each cluster? Write your answer in the form "Number of answers in Cluster N) [Number of answers in cluster N]":

Number of answers in cluster 1)"""


def candidates(
    answers: Sequence[str], prefix: str = "Answer", separator: str = "\n"
) -> str:
    return separator.join(
        (f"{prefix} {idx}) {answer.strip()}" for idx, answer in enumerate(answers, 1))
    )


def build_cluster_prompt(question: str, answers: Sequence[str]) -> str:
    prefix = CLUSTER_PREFIX.format(question=question)
    return "\n\n".join(
        (prefix, candidates(answers), CLUSTER_DIRECTIONS.format(question=question))
    )


def build_count_prompt(question: str, answers: Sequence[str], clusters: str) -> str:
    cluster_prompt = build_cluster_prompt(question, answers)
    return "\n\n".join((cluster_prompt + clusters.rstrip(), COUNT_DIRECTIONS))


def build_final_prompt(
    question: str, answers: Sequence[str], clusters: str, counts: str
):
    count_prompt = build_count_prompt(question, answers, clusters)
    return "\n\n".join(
        (
            count_prompt + counts.rstrip(),
            f"After this clustering procedure, we can conclude that the most popular answer to the question '{question}' is:\n\n",
        )
    )
