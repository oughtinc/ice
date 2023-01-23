from collections.abc import Mapping
from collections.abc import Sequence
from typing import Optional
from typing import TypedDict
from typing import Union

from ice.formatter.multi import format_multi
from ice.formatter.multi import stop
from ice.formatter.multi import StopSentinel
from ice.formatter.transform.value import numbered_list
from ice.formatter.transform.value import ValueTransform
from ice.recipes.program_search.nodes.select.dynamic import SelectionExample

NONE_ANSWER = "None of the new excerpts are needed to answer the question."

EXAMPLES: list[dict[str, Union[str, ValueTransform, StopSentinel]]] = [
    dict(
        question="What was the effect size?",
        existing=numbered_list(
            [
                """This training [of medical students and trainees] requires acquiring skills to analyze and extract imaging features to identify patterns, generate a differential diagnosis that matches the patterns, and correlate the imaging features and differential with clinical findings to select the most likely diagnosis [5].""",
                """However, owing to time constraints, training opportunities might be compressed, and trainees may not be able to access as many images as their tutors or teachers [medical students and trainees need to learn several kinds of images to achieve an expert level].""",
                """Individual variability [in learning styles] is thought to substantially affect learning styles [6,7].""",
                """Moreover, learning [for medical students and trainees] is dictated by the number and diversity of cases encountered, with varying practices and patient mixes.""",
                """An artificial intelligence (AI)-assisted teaching platform can deliver personalized education and 24-h supervised tutoring that benefits both trainees [medical students and] and trainers [teachers].""",
            ]
        ),
        texts=numbered_list(
            [
                """The WithAI score [of the medical students in the AIL group] (88.87 ± 5.51) was significantly higher than the prelearning score [of the medical students in the AIL group] (75.73 ± 10.58, p < 0.01).""",
            ]
        ),
        selections=NONE_ANSWER,
        NONE_ANSWER=NONE_ANSWER,
    ),
    dict(
        question="What was the design of the Ghana experiment?",
        existing=numbered_list(
            [
                """Of the six experiments, three are individual randomized trials with randomization at the household level within each village (India, Ethiopia and Pakistan) and three are clustered randomized trials, with randomization at both the village and household level (Ghana, Honduras, and Peru).""",
                """In the countries with clustered randomization, villages were randomly selected to be treatment or control villages, and then treatment households were randomly selected within the set of eligible households in treatment villages.""",
            ]
        ),
        texts=numbered_list(
            [
                """One site (Ghana) had a more complex design with two additional treatment groups (savings only, and productive asset grant only) to “unpack” those aspects of the intervention.""",
                """In this paper we are using only the group that received the pooled intervention.""",
                """The sample size used in the analysis varies from 925 households (Ethiopia) to 2,606 households (Ghana) from site to site.""",
                """Table S1b presents baseline data for the same variables and indices used as the primary outcome measures.""",
                """Panel A presents the mean comparisons and t-tests for equality of means.""",
            ]
        ),
        selections="1",
        NONE_ANSWER=NONE_ANSWER,
    ),
    dict(
        question="What was the sample size?",
        existing=numbered_list(
            [
                """METHODS: Medical outcome of 8-year-old singletons (n = 150) born through ICSI (³32 weeks) was compared with that of 147 singletons of the same age born after spontaneous conception (SC) [in order to investigate possible health problems in the long-term outcome of children born after ICSI].""",
            ]
        ),
        texts=numbered_list(
            [
                """Information about their [the 8-year-old singletons born through ICSI's] general health was obtained from the parents by means of a questionnaire.""",
                """RESULTS: Fifteen of 150 ICSI children [8-year-old singletons born through ICSI] experienced a major congenital malformation compared with 5/147 SC children [of the same age born after spontaneous conception] (P < 0.05).""",
                """Pubertal staging [of 8-year-old singletons born through ICSI and of the same age born after spontaneous conception] was similar in both groups.""",
                """Neurological examination did not show important differences between ICSI [8-year-old singletons born through ICSI] and SC [of the same age born after spontaneous conception] children.""",
                """ICSI children [8-year-old singletons born through ICSI] did not require more remedial therapy or surgery or hospitalization than SC children [of the same age born after spontaneous conception].""",
                """CONCLUSION: Physical examination including a thorough neurological examination did not reveal important differences between the two groups [of 8-year-old singletons, one group born through ICSI and the other group born after spontaneous conception].""",
            ]
        ),
        selections=NONE_ANSWER,
        NONE_ANSWER=NONE_ANSWER,
    ),
]

PREFACE = f'Instructions: You are selecting some excerpts to provide as context to someone who will need to answer each question. They should receive exactly the excerpts they need, with no extra excerpts that are redundant or that do not answer the exact question being asked. For each question, you can select exactly one new excerpt to provide to the person who will use these excerpts to answer the question, in addition to the excerpts they already have (if any). If none of the new excerpts answer the exact question asked, or the excerpts they already have do answer the question fully, say "{NONE_ANSWER}".'

EXAMPLE_TEMPLATE = """
Question: {question}

Excerpts the person answering the question already has access to:

{existing}

Additional excerpts, from which you will choose one at most to add to the excerpts they already have, only if it answers the question:

{texts}

Excerpt to add to the already chosen excerpts (if they can already answer the question or none of these excerpts answer the question, say "{NONE_ANSWER}"): {selections}"""


# pretty diverse questions
# some examples with none
# some examples with best out of multiple okay candidates


class RenderableSelectionExample(TypedDict):
    question: str
    existing: Union[ValueTransform, str]
    texts: Union[ValueTransform, str]
    selections: str
    NONE_ANSWER: str


NO_EXISTING = "(no excerpts selected so far)"


def render_selection_example(
    question: str, example: SelectionExample
) -> RenderableSelectionExample:
    return RenderableSelectionExample(
        question=question,
        existing=numbered_list(example.existing) if example.existing else NO_EXISTING,
        texts=numbered_list([str(text) for text in example.selection]),
        selections=NONE_ANSWER
        if not example.positive_idxs
        else str(example.positive_idxs[0] + 1),
        NONE_ANSWER=NONE_ANSWER,
    )


# async def examples_from_gold_standard(
#     question: str,
#     texts: Sequence[Selection],
#     gs_quotes: Sequence[str],
#     *,
#     n: int,
#     step: int,
#     max_existing: int,
# ) -> Sequence[RenderableSelectionExample]:
#     examples = await make_examples(
#         texts, gs_quotes, n=n, step=step, max_existing=max_existing
#     )
#     return [
#         render_selection_example(question, example)
#         for example in (
#             first_positive_example(examples),
#             best_negative_example(examples),
#         )
#         if example
#     ]


# async def varied_examples_from_gold_standards(
#     standards: Sequence[tuple[str, Sequence[Selection], Sequence[str]]],
#     *,
#     n: int,
#     step: int,
# ) -> Sequence[RenderableSelectionExample]:
#     max_existing = cycle(range(5))
#     which_example = cycle((0, -1))
#     examples: list[RenderableSelectionExample] = []
#     for question, texts, gs_quotes in standards:
#         new_examples = await examples_from_gold_standard(
#             question, texts, gs_quotes, n=n, step=step, max_existing=next(max_existing)
#         )
#         if new_examples:
#             examples.append(new_examples[next(which_example)])
#     return examples


def make_selection_prompt(
    *,
    question: str,
    existing: Sequence[str],
    texts: Sequence[str],
    examples: Optional[list[RenderableSelectionExample]] = None,
) -> str:
    all_examples = (examples or EXAMPLES) + [
        dict(
            question=question,
            existing=numbered_list(existing) if existing else NO_EXISTING,
            texts=numbered_list(texts),
            selections=stop("None"),
            NONE_ANSWER=NONE_ANSWER,
        )
    ]
    filled_examples = format_multi(EXAMPLE_TEMPLATE, all_examples)  # type: ignore[arg-type]
    prompt = "\n\n".join((PREFACE, "\n\n---\n\n".join(filled_examples)))
    return prompt


def get_selections(
    logprobs: dict[str, float], num_selections: int
) -> Mapping[int, float]:
    """Logprobs for space-leading integer tokens from the openai response"""
    # TODO: Rethink this, come up with a more theoretically sound method
    assert num_selections < 362, "Tokenization method assumes num_selections < 362"
    return {i: logprobs.get(f" {i + 1}", float("-inf")) for i in range(num_selections)}
