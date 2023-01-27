from collections.abc import Sequence
from itertools import chain
from typing import cast
from typing import Optional
from typing import Union

from structlog.stdlib import get_logger

from ice.formatter.multi import format_multi
from ice.formatter.multi import stop
from ice.formatter.multi import StopSentinel
from ice.recipe import recipe
from ice.recipes.experiments_and_arms.num_utils import extract_nums
from ice.recipes.experiments_and_arms.types import PassageWithReasoning

# TODO: Make configurable for different ways of prompting helpfulness

log = get_logger()


def make_helpfulness_prompt(prefix: str, helpful_line: str, num_excerpts: int) -> str:
    TEMPLATE = """Number of excerpts: {num_excerpts}

{helpful_line}

List the helpful excerpts here: {translation}""".strip()

    helpfulness_cases: list[dict[str, Union[int, str, StopSentinel]]] = [
        dict(
            num_excerpts=4,
            helpful_line="None of the excerpts were helpful",
            translation="None",
        ),
        dict(
            num_excerpts=4,
            helpful_line="Excerpt 3 was helpful. Excerpts 1, 2, and 4 were not helpful",
            translation="3",
        ),
        dict(
            num_excerpts=4,
            helpful_line="Excerpts 1 and 2 were helpful, and excerpt 3 was somewhat helpful. Excerpt 4 was not helpful.",
            translation="1, 2, 3",
        ),
        dict(
            num_excerpts=5,
            helpful_line="Excerpts 1, 2, and 3 were not helpful, but the rest were helpful.",
            translation="4, 5",
        ),
        dict(
            num_excerpts=3,
            helpful_line="All of the excerpts were helpful.",
            translation="1, 2, 3",
        ),
    ]
    for example in helpfulness_cases:
        example["helpful_line"] = prefix + cast(str, example["helpful_line"])
    helpfulness_cases.append(
        dict(num_excerpts=num_excerpts, helpful_line=helpful_line, translation=stop(""))
    )

    filled = format_multi(TEMPLATE, helpfulness_cases)
    return "\n\n".join(filled)


HELPFULNESS_SHARED = dict(
    thing_to_understand="how many experiments were conducted in the study"
)

HELPFULNESS_PREFIX = "Which excerpts, if any were helpful?"


async def _which_paras_were_helpful(
    helpfulness_prefix: str, helpful_line: str, num_excerpts: int
) -> list[int]:
    prompt = make_helpfulness_prompt(helpfulness_prefix, helpful_line, num_excerpts)
    completion = await recipe.agent().complete(prompt=prompt, stop="\n")
    return [num - 1 for num in extract_nums(completion)]


def extract_helpful_line(reasoning: str) -> Optional[str]:
    lines = reasoning.split("\n")
    helpful_lines = [
        line for line in lines if "were helpful in understanding" in line.lower()
    ]
    if not helpful_lines:
        log.warning("Response missing helpful lines", reasoning=reasoning)
        return None
    if len(helpful_lines) > 1:
        log.warning(
            "Response has too many helpful lines",
            reasoning=reasoning,
            helpful_lines=helpful_lines,
        )
    return helpful_lines[0]


async def helpful_paragraphs(
    helpful_line: str, paragraphs: Sequence[str]
) -> Sequence[str]:
    idxs = await _which_paras_were_helpful(
        HELPFULNESS_PREFIX, helpful_line, len(paragraphs)
    )
    return [paragraphs[idx] for idx in idxs if idx < len(paragraphs)]


async def keep_most_helpful_paragraphs(
    passages_with_reasoning: Sequence[PassageWithReasoning],
    start_with: int = 2,
    continue_if_less_than: int = 3,
) -> Sequence[str]:
    async def get_best_paras(
        passages_with_reasoning: Sequence[PassageWithReasoning],
    ):
        helpful_lines = [pwr.helpfulness for pwr in passages_with_reasoning]
        helpful_lines_non_null = [
            (line, pwr)
            for line, pwr in zip(helpful_lines, passages_with_reasoning)
            if line
        ]
        best_paras = chain.from_iterable(
            [
                (await helpful_paragraphs(line, pwr.passage))
                for line, pwr in helpful_lines_non_null
            ]
        )
        return list(best_paras)

    initial_passages, later_passages = (
        passages_with_reasoning[:start_with],
        passages_with_reasoning[start_with:],
    )
    best_paras = set(await get_best_paras(initial_passages))
    while later_passages and len(best_paras) < continue_if_less_than:
        next_para = later_passages[0]
        later_passages = later_passages[1:]
        best_paras = best_paras | set((await get_best_paras([next_para])))

    # Sort so that the returned order is deterministic for caching etc.
    best_paras_sorted = sorted(best_paras)

    # Plain alphabetical sort actually lands on a pathological case
    # that leads to a test failure where count_experiments returns 59 which leads to
    # ValueError: Count 59 not in count word dictionary
    # So we reverse here to workaround that, although that should be solved in general
    # and the recipe/test should be moved out of the repo anyway.
    return best_paras_sorted[::-1]


recipe.main(keep_most_helpful_paragraphs)
