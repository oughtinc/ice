import math
from collections.abc import Mapping
from collections.abc import Sequence
from typing import cast
from typing import Optional
from typing import TypedDict
from typing import Union

from ice.formatter.multi import format_multi
from ice.formatter.multi import stop
from ice.formatter.multi import StopSentinel
from ice.formatter.transform.value import numbered_list
from ice.formatter.transform.value import ValueTransform

REASONINGS: list[str] = [
    """- Excerpt 1 talks about the training of medical students and trainees and so is not related to effect size.
- Excerpt 2 talks about the need for medical trainees to learn from different kinds of images to attain expert level this is also not relevant to effect size.
- Excerpt 3 talks about how individual variability substantially affects learning styles this is also not relevant to effect size.
- Excerpt 4 says that learning is dictated by the diversity and number of cases  encountered this is again relevant to effect size.
- Excerpt 5 talks the benefits of an AI assisted teaching platform. This is irrelevant to the effect size.
- Excerpt 6 talks about the WithAI score (88.87) of the medical students in the AIL group being significantly higher than the prelearning score (75.73). This directly related to the effect size.
Which excerpts answer the question, from most to least important: 6""",
    """- Excerpt 1 talks about the six experiments and states that the Ghana experiment is a clustered randomized trial. This is relevant to the design of the Ghana experiment.
- Excerpt 2 talks about the Ghana experiment having a more complex design with two additional treatment groups. This is very much relevant to the design of the Ghana experiment.
- Excerpt 3 says that in this paper, they  are using only the group that received the pooled intervention. This is not relevant to the to the design of the Ghana experiment.
- Excerpt 4 talks about the sample size used in the analysis, which could relate design of the Ghana experiment but it's not the most important detail.
- Excerpt 5 presents the baseline data for the same variables and indices used as the primary outcome measures, which is not relevant to the design of the Ghana experiment .
- Excerpt 6 says that Panel A presents the mean comparisons and t-tests for equality of means, which is not relevant to the design of the Ghana experiment.
- Excerpt 7 talks about how villages were randomly selected to be treatment or control villages in the countries with clustered randomization. This is relevant to the question.
Which excerpts answer the question, from most to least important: 2, 1, 7, 4""",
    """- Excerpt 1 talks about how information about the general health of 8-year-old singletons born through ICSI was obtained from the parents by means of a questionnaire. This is not relevant to the sample size.
- Excerpt 2 states that 15 out of 150 ICSI children experienced a major congenital malformation compared with 5/147 SC children. This excerpt includes the sample size for both the ICSI children and the SC children and is hence directly relevant to the question.
- Excerpt 3 says that pubertal staging was similar in both groups. This is not relevant to the sample size.
- Excerpt 4 says that neurological examination did not show important differences between ICSI and SC children. This is not relevant to the sample size.
- Excerpt 5 states that ICSI children did not require more remedial therapy or surgery or hospitalization than SC children. This is not relevant to the sample size.
- Excerpt 6 talks about how the medical outcome of 8-year-old singletons born through ICSI was compared with that of 147 singletons of the same age born after spontaneous conception. This excerpt includes the sample size for both the ICSI children and the SC children and relevant to the sample size.
- Excerpt 7 is the conclusion of the study and it says that physical examination including a thorough neurological examination did not reveal important differences between the two groups. This is not relevant to the sample size.
Which excerpts answer the question, from most to least important: 2, 6""",
]

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
                """The WithAI score [of the medical students in the AIL group] (88.87 ± 5.51) was significantly higher than the prelearning score [of the medical students in the AIL group] (75.73 ± 10.58, p < 0.01).""",
            ]
        ),
        reasoning_with_selection=REASONINGS[0],
        selections="6",
    ),
    dict(
        question="What was the design of the Ghana experiment?",
        existing=numbered_list(
            [
                """Of the six experiments, three are individual randomized trials with randomization at the household level within each village (India, Ethiopia and Pakistan) and three are clustered randomized trials, with randomization at both the village and household level (Ghana, Honduras, and Peru).""",
                """One site (Ghana) had a more complex design with two additional treatment groups (savings only, and productive asset grant only) to “unpack” those aspects of the intervention.""",
                """In this paper we are using only the group that received the pooled intervention.""",
                """The sample size used in the analysis varies from 925 households (Ethiopia) to 2,606 households (Ghana) from site to site.""",
                """Table S1b presents baseline data for the same variables and indices used as the primary outcome measures.""",
                """Panel A presents the mean comparisons and t-tests for equality of means.""",
                """In the countries with clustered randomization, villages were randomly selected to be treatment or control villages, and then treatment households were randomly selected within the set of eligible households in treatment villages.""",
            ]
        ),
        texts=numbered_list([]),
        reasoning_with_selection=REASONINGS[1],
        selections="2, 1, 7, 4",
    ),
    dict(
        question="What was the sample size?",
        existing=numbered_list(
            [
                """Information about their [the 8-year-old singletons born through ICSI's] general health was obtained from the parents by means of a questionnaire.""",
                """RESULTS: Fifteen of 150 ICSI children [8-year-old singletons born through ICSI] experienced a major congenital malformation compared with 5/147 SC children [of the same age born after spontaneous conception] (P < 0.05).""",
                """Pubertal staging [of 8-year-old singletons born through ICSI and of the same age born after spontaneous conception] was similar in both groups.""",
                """Neurological examination did not show important differences between ICSI [8-year-old singletons born through ICSI] and SC [of the same age born after spontaneous conception] children.""",
                """ICSI children [8-year-old singletons born through ICSI] did not require more remedial therapy or surgery or hospitalization than SC children [of the same age born after spontaneous conception].""",
                """METHODS: Medical outcome of 8-year-old singletons (n = 150) born through ICSI (³32 weeks) was compared with that of 147 singletons of the same age born after spontaneous conception (SC) [in order to investigate possible health problems in the long-term outcome of children born after ICSI].""",
                """CONCLUSION: Physical examination including a thorough neurological examination did not reveal important differences between the two groups [of 8-year-old singletons, one group born through ICSI and the other group born after spontaneous conception].""",
            ]
        ),
        reasoning_with_selection=REASONINGS[2],
        selections="6, 2",
    ),
]

INSTRUCTIONS = """Instructions: For each question and list of excerpts, record which excerpts help answer the question, from most to least important."""

EXAMPLE_TEMPLATE = """
Question: {question}

Excerpts:

{existing}

Which excerpts answer the question, from most to least important: {selections}
""".strip()

EXAMPLE_WITH_REASONING_TEMPLATE = """
Question: {question}

Excerpts:

{existing}

Let's think about how each excerpt relates to the question.

{reasoning_with_selection}
""".strip()


EXAMPLE_SEPARATOR = "\n\n---\n\n"


class RenderablePruningExample(TypedDict):
    question: str
    existing: ValueTransform[Sequence[str]]
    selections: str


def make_pruning_prompt(
    *,
    question: str,
    existing: Sequence[str],
    examples: Optional[list[RenderablePruningExample]] = None,
) -> str:
    all_examples = (examples or EXAMPLES) + [
        dict(
            question=question,
            existing=numbered_list(existing),
            selections=stop(""),
        )
    ]
    filled_examples = format_multi(EXAMPLE_TEMPLATE, all_examples)  # type: ignore[arg-type]
    prompt = "\n\n".join((INSTRUCTIONS, EXAMPLE_SEPARATOR.join(filled_examples)))
    return prompt


def make_pruning_with_reasoning_prompt(
    *,
    question: str,
    existing: Sequence[str],
) -> str:
    all_examples = EXAMPLES[1:2] + [
        dict(
            question=question,
            existing=numbered_list(existing),
            reasoning_with_selection=stop("- Excerpt 1"),
        )
    ]
    filled_examples = format_multi(EXAMPLE_WITH_REASONING_TEMPLATE, all_examples)
    prompt = "\n\n".join((INSTRUCTIONS, EXAMPLE_SEPARATOR.join(filled_examples)))
    return prompt


class _LogProbsOpenAI(TypedDict):
    tokens: list[str]
    token_logprobs: list[float]
    top_logprobs: list[dict[str, float]]


def get_pruned_selections_via_logprobs(
    logprobs: dict, num_selections: int
) -> Mapping[int, float]:
    """Returns a mapping of scores where the
    integer part is the descending rank and
    the decimal part is the probability.

    Args:
        logprobs (dict): openai_response["choices"][0]["logprobs"]
        num_selections (int): number of candidates for pruning

    Returns:
        Mapping[int, float]: scores for each candidate, with "-inf" meaning "not present"
    """
    assert num_selections < 362
    lps = cast(_LogProbsOpenAI, logprobs)
    # Don't include tokens from reasoning
    start_idx = len(lps["tokens"]) - list(reversed(lps["tokens"])).index(" important")
    selections = [
        idx
        for idx, selection in enumerate(lps["tokens"])
        if selection.strip().isnumeric() and idx >= start_idx
    ]
    indexed_probs: dict[int, float] = {}
    for rank, selected_idx in enumerate(selections):
        for candidate in range(num_selections):
            if candidate not in indexed_probs:
                prob_at_position = lps["top_logprobs"][selected_idx].get(
                    f" {candidate + 1}"
                )
                if prob_at_position is not None:
                    indexed_probs[candidate] = (
                        len(selections) - rank + math.exp(prob_at_position)
                    )
    return {i: indexed_probs.get(i) or float("-inf") for i in range(num_selections)}


def get_pruned_selections_via_completion(completion: str) -> Sequence[int]:
    return list(map(lambda i: int(i.strip()) - 1, completion.split(",")))
