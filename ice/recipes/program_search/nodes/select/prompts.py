from ice.formatter.multi import format_multi, stop, StopSentinel
from ice.formatter.transform.value import ValueTransform, numbered_list
from typing import Mapping, Sequence


EXAMPLES: list[dict[str, str | ValueTransform | StopSentinel]] = [
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
        selections="(none)",
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
        selections="(none)",
    ),
]

PREFACE = 'Instructions: Selecting which new excerpts are needed, in addition to already selected excerpts, to answer the question. If none of the new excerpts are helpful or the already selected excerpts already fully answer the question, answer "(none)"'

EXAMPLE_TEMPLATE = """
Question: {question}
Already selected excerpts: {existing}
New excerpts: {texts}
New excerpts needed to answer the question (from most to least helpfulness): {selections}"""


# pretty diverse questions
# some examples with none
# some examples with best out of multiple okay candidates


def make_selection_prompt(
    *, question: str, existing: Sequence[str], texts: Sequence[str]
) -> str:
    examples = EXAMPLES + [
        dict(
            question=question,
            existing=numbered_list(existing),
            texts=numbered_list(texts),
            selections=stop("("),
        )
    ]
    filled_examples = format_multi(EXAMPLE_TEMPLATE, examples)
    prompt = "\n\n".join((PREFACE, "\n\n".join(filled_examples)))
    return prompt


def get_selections(
    logprobs: dict[str, float], num_selections: int
) -> Mapping[int, float]:
    """Logprobs for space-leading integer tokens from the openai response"""
    # TODO: Rethink this, come up with a more theoretically sound method
    assert num_selections < 362, "Tokenization method assumes num_selections < 362"
    return {i: logprobs.get(f" {i + 1}", float("-inf")) for i in range(num_selections)}
