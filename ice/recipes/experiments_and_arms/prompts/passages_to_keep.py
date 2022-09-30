from ice.recipe import recipe
from typing import Sequence
from ice.recipes.experiments_and_arms.num_utils import extract_nums
from ice.recipes.experiments_and_arms.types import PassageWithReasoning
from itertools import chain

from ice.formatter.multi import stop, StopSentinel, format_multi
from ice.trace import trace
from typing import Sequence, cast
from structlog.stdlib import get_logger
from ice.recipe import recipe

## TODO: Make configurable for different ways of prompting helpfulness

log = get_logger()


def make_helpfulness_prompt(prefix: str, helpful_line: str) -> str:
    TEMPLATE = """{helpful_line}

List them here: {translation}""".strip()

    helpfulness_cases: list[dict[str, str | StopSentinel]] = [
        dict(helpful_line="None of the excerpts were helpful", translation="None"),
        dict(
            helpful_line="Excerpt 3 was helpful. Excerpts 1, 2, and 4 were not helpful",
            translation="3",
        ),
        dict(
            helpful_line="Excerpts 1 and 2 were helpful, and excerpt 3 was somewhat helpful. Excerpt 4 was not helpful.",
            translation="1, 2, 3",
        ),
        dict(
            helpful_line="Excerpts 3 and 4 were somewhat helpful. Excerpts 1 and 2 were not helpful.",
            translation="3, 4",
        ),
    ]
    for example in helpfulness_cases:
        example["helpful_line"] = prefix + example["helpful_line"]
    helpfulness_cases.append(dict(helpful_line=helpful_line, translation=stop("")))

    filled = format_multi(TEMPLATE, helpfulness_cases)
    return "\n\n".join(filled)


HELPFULNESS_TEMPLATE = "Which excerpts, if any, were helpful in understanding {thing_to_understand}? {helpful_line}"

HELPFULNESS_SHARED = dict(
    thing_to_understand="how many experiments were conducted in the study"
)

HELPFULNESS_PREFIX = "Which excerpts, if any were helpful in understanding how many experiments were conducted in the study?"


async def _which_paras_were_helpful(
    helpfulness_prefix: str, helpful_line: str
) -> list[int]:
    prompt = make_helpfulness_prompt(helpfulness_prefix, helpful_line)
    completion = await recipe.agent().answer(prompt=prompt, multiline=False)
    return [num - 1 for num in extract_nums(completion)]


def extract_helpful_line(reasoning: str) -> str | None:
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
    idxs = await _which_paras_were_helpful(HELPFULNESS_PREFIX, helpful_line)
    return [paragraphs[idx] for idx in idxs if idx < len(paragraphs)]


async def most_helpful_paragraphs(
    passages_with_reasoning: Sequence[PassageWithReasoning],
    start_with: int = 2,
    continue_if_less_than: int = 3,
) -> Sequence[str]:
    async def get_best_paras(
        passages_with_reasoning: Sequence[PassageWithReasoning],
    ):
        helpful_lines = [
            pwr.helpfulness for pwr in passages_with_reasoning
        ]
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
    return [p for p in best_paras]

recipe.main(most_helpful_paragraphs)