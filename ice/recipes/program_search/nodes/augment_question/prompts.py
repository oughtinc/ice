import re
from collections.abc import Sequence
from typing import Optional
from typing import TypedDict
from typing import Union

from structlog.stdlib import get_logger

from ice.formatter.multi import format_multi
from ice.formatter.multi import stop
from ice.formatter.multi import StopSentinel
from ice.formatter.transform.value import numbered_list
from ice.formatter.transform.value import ValueTransform

log = get_logger()


EXAMPLES: list[dict[str, Union[str, ValueTransform, StopSentinel]]] = [
    dict(
        question="What was the effect size?",
        selections=numbered_list(
            [
                """The WithAI score (88.87 ± 5.51) was significantly higher than the prelearning score  (75.73 ± 10.58, p < 0.01).""",
            ]
        ),
        reasoning="""We know that the WithAI score of 88.87 ± 5.51 was significantly higher than the prelearning score 75.73 ± 10.58, with p < 0.01). In order to answer the question fully, we should understand how the prelearning score and the WithAI scores were measured. We should also learn more about the intervention this difference applied to and whether other measures were included in the analysis.""",
        additional_questions=numbered_list(
            [
                "How was the prelearning score measured?",
                "How was the WithAI score measured?",
                "What intervention did the WithAI and prelearning scores apply to?",
                "In addition to the difference between the WithAI and prelearning scores, were there any other measures included in the analysis, and what were their effect sizes?",
            ]
        ),
        most_important_question="4: In addition to the difference between the WithAI and prelearning scores, were there any other measures included in the analysis, and what were their effect sizes?",
    ),
    dict(
        question="What was the design of the Ghana experiment?",
        selections=numbered_list(
            [
                """Of the six experiments, three are individual randomized trials with randomization at the household level within each village (India, Ethiopia and Pakistan) and three are clustered randomized trials, with randomization at both the village and household level (Ghana, Honduras, and Peru).""",
                """In the countries with clustered randomization, villages were randomly selected to be treatment or control villages, and then treatment households were randomly selected within the set of eligible households in treatment villages.""",
            ]
        ),
        reasoning="""We know that of the six experiments, three were individual randomized trials and three were clustered randomized trials. We also know that, in the countries with clustered randomization, villages were randomly selected to be treatment or control villages, and then treatment households were randomly selected within the set of eligible households in treatment villages. In order to answer the question fully, we should understand how the villages and households were selected in the individual randomized trials, and what the eligibility criteria were for households in the clustered randomized trials.""",
        additional_questions=numbered_list(
            [
                "How were villages and households selected in the Ghana experiment?",
                "What were the eligibility criteria for villages and households in the Ghana experiment?",
                "What were the treatment and control conditions in the clustered randomized trials, especially the Ghana experiment?",
                "What was the timing and duration of the Ghana experiment?",
            ]
        ),
        most_important_question="3: What were the treatment and control conditions in the clustered randomized trials, especially the Ghana experiment?",
    ),
]

PREFACE = "Instructions: For each question we have been asked to answer, we have been given some excerpts from a document containing the answer. Brainstorm 1-5 additional questions that would help us select more excerpts from the document, and then identify which of these questions would be most helpful to understand in order to be able to fully answer the original question."

EXAMPLE_TEMPLATE = """
Question we have been asked to answer: {question}

Excerpts from the document we have been given so far:

{selections}

What we know from these excerpts, and what additional information would help us answer the question: {reasoning}

1-5 additional questions to seek information on to answer the question we have been asked to answer:

{additional_questions}

Out of these questions, the question that would be most helpful to gather additional information about is question {most_important_question}""".strip()

EXAMPLE_SEPARATOR = "\n\n---\n\n"


prompt = "\n\n".join(
    (PREFACE, "\n\n---\n\n".join(format_multi(EXAMPLE_TEMPLATE, EXAMPLES)))
)


class RenderableAugmentQuestionExample(TypedDict):
    question: str
    selections: ValueTransform[Sequence[str]]
    reasoning: str
    additional_questions: ValueTransform[Sequence[str]]
    most_important_question: str


def make_augment_question_prompt(
    *,
    question: str,
    existing_selections: Sequence[str],
    examples: Optional[list[RenderableAugmentQuestionExample]] = None,
) -> str:
    all_examples = (examples or EXAMPLES) + [
        dict(
            question=question,
            selections=numbered_list(existing_selections),
            reasoning=stop(""),
        )
    ]
    filled_examples = format_multi(EXAMPLE_TEMPLATE, all_examples)  # type: ignore[arg-type]
    prompt = "\n\n".join((PREFACE, EXAMPLE_SEPARATOR.join(filled_examples)))
    return prompt


def strip_enumeration_prefix(text: str) -> str:
    return re.sub(r"^\w*\s*\d+(\.|\))", "", text.strip()).strip()


def get_new_questions(completion: str) -> tuple[str, Sequence[str]]:
    # This is intentionally fragile to failure to follow the prompt format to first see how often/how it occurs
    _, remaining_part = completion.split("we have been asked to answer:")
    try:
        questions_list, remaining_part = remaining_part.split(
            "Out of these questions, the question that would be most helpful to gather additional information about is question "
        )
        num = int(remaining_part.split(":")[0].strip())
        questions = list(
            filter(
                None,
                (strip_enumeration_prefix(line) for line in questions_list.split("\n")),
            )
        )
        return questions[num - 1], questions
    except ValueError:
        log.warning("Unexpected response", completion=completion)
        questions = [
            strip_enumeration_prefix(line)
            for line in remaining_part.split("\n")
            if line and line[0].isnumeric()
        ]
        return questions[0], questions
