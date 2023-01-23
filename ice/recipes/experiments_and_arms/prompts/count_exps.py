from collections.abc import Sequence
from collections.abc import Sized
from typing import Optional
from typing import Union

from structlog.stdlib import get_logger

from ice.formatter.multi import format_multi
from ice.formatter.multi import stop
from ice.formatter.multi import StopSentinel
from ice.formatter.transform.dependent import DependentTransform
from ice.formatter.transform.dependent import plural_transform
from ice.formatter.transform.positional import OrdinalWord
from ice.formatter.transform.value import numbered_list
from ice.formatter.transform.value import ValueTransform
from ice.recipes.experiments_and_arms.num_utils import extract_nums
from ice.recipes.experiments_and_arms.prompts.utils import get_part
from ice.recipes.experiments_and_arms.types import MultipartReasoningPrompt

log = get_logger()

COUNT_EXPERIMENTS_PREFACE = """When evaluating a randomized controlled trial, you should first identify the number of distinct experiments (e.g., randomized controlled trials, or RCTs) conducted. An experiment is where the authors evaluate the effect of some program, action, or substance on a population. Two experiments are distinct if they are conducted on different populations. Experiments have different "trial arms". Trial arms describe the different treatment conditions participants were in.

Let's look at excerpts from five different papers to see what information, if any, they provide about the study's experiments (e.g., RCTs). We'll have to identify what each extract tells us about whether the authors conducted one or several experiments. If there is no explicit information indicating that multiple experiments or studies were conducted, assume there was just one experiment.""".strip()

COUNT_EXPERIMENTS_EXAMPLE_TEMPLATE = """
{ordinal}, consider the following excerpt{maybe_plural_excerpts} from a paper:

{paragraphs}

Let's think about what each excerpt tells us, if anything, about the number of experiments (e.g., RCTs): {reasoning}

Here's all the information in this paper about how many experiments there were: {answer}
""".strip()

COUNT_EXPERIMENTS_EXAMPLES: list[
    dict[str, Union[ValueTransform[Sequence[str]], str]]
] = [
    dict(
        paragraphs=numbered_list(
            [
                """Table 3 shows the various comparisons that were made between the treatment groups. To examine the effect of iron supplementation, groups 3 and 5 were comp~red with groups 2 and 4, as the treatments given to those in the former groups were identical to the treatments given to those in the latter groups apart from the addition of iron to groups 3 and 5 (Table 2 ). Similarly the effect of folic acid was examined by comparing groups 2 and 3 with groups 4 and 5. The third comparison in Table 3 was made to determine whether any interaction between iron and folate effects existed. The effect of antimalarials was examined using two comparisons. First, group 1 was compared with group 2, the treatments given to patients in these groups being identical apart from the addition of antimalarials to group 2. Secondly, patients in group 1 were compared with those in groups 2 to 5 combined: this was done only when there was no marked effect of iron or folic acid on the variable being examined.""",
                """To test each comparison for statistical significance, t-tests were performed for continuous variables, and chi-squared tests for binary variables (with a continuity correction). For binary variables for which any expected frequency was less than 5, Fisher's exact test (2-sided) was performed.""",
                """Logarithmic transformations were made for SFA, RCF, serum B 12 and reticulocyte counts before analysis, as the distributions of these variables were skewed, but they have been re-transformed to the original scale for presentation.""",
                """There were no significant differences in any haematological measurement between the five groups when the patients were entered into the trial (Table 4 ). Ninety-one patients (45•5%) were anaemic. Four patients only had totally normal red cells on the blood film; most commonly seen were moderate ( + +) anisocytosis, with mild ( +) macrocytosis, microcytosis and polychromasia, as described previously (Fleming et al., 1984). Six subjects had elliptocytosis not associated with anaemia. Fifty-one (25•5%) had sickle cell trait, with nine to 12 individuals in each of the five groups: two had Hb-AC (groups 1 and 5). Malaria, predominantly P.falciparum, was observed in 53 (26•5%) of subjects. There was only one significant difference in frequency of parasite density between the treatment groups; P.falciparum gametocytes were more frequent in groups 3 and 5 (to receive iron supplements) than in groups 2 and 4 (not to receive iron supplements) (Table 5) Mean±s.D. t' "' two (60•4%) with malaria were anaemic, compared to 59 (40•1 %) without parasitaemia""",
            ]
        ),
        reasoning="""Excerpt 1 discusses various comparisons made between treatment groups. Because these groups are being compared directly, this indicates that they are part of the same study. Excerpt two just explains the statistical significance test use. Excerpt 3 indicates the data transformations used for variables. Exceprt 4 discusses different haematological measurements take in the study, and how frequently different conditions were observed in the different groups.""",
        answer="""Because there is no explicit indication otherwise, these excerpts indicate that the study conducted one experiment. Final Answer: 1.""",
    ),
    dict(
        paragraphs=numbered_list(
            [
                """Table 3 shows the various comparisons that were made between the treatment groups. To examine the effect of iron supplementation, groups 3 and 5 were comp~red with groups 2 and 4, as the treatments given to those in the former groups were identical to the treatments given to those in the latter groups apart from the addition of iron to groups 3 and 5 (Table 2 ). Similarly the effect of folic acid was examined by comparing groups 2 and 3 with groups 4 and 5. The third comparison in Table 3 was made to determine whether any interaction between iron and folate effects existed. The effect of antimalarials was examined using two comparisons. First, group 1 was compared with group 2, the treatments given to patients in these groups being identical apart from the addition of antimalarials to group 2. Secondly, patients in group 1 were compared with those in groups 2 to 5 combined: this was done only when there was no marked effect of iron or folic acid on the variable being examined.""",
                """To test each comparison for statistical significance, t-tests were performed for continuous variables, and chi-squared tests for binary variables (with a continuity correction). For binary variables for which any expected frequency was less than 5, Fisher's exact test (2-sided) was performed.""",
                """Logarithmic transformations were made for SFA, RCF, serum B 12 and reticulocyte counts before analysis, as the distributions of these variables were skewed, but they have been re-transformed to the original scale for presentation.""",
                """There were no significant differences in any haematological measurement between the five groups when the patients were entered into the trial (Table 4 ). Ninety-one patients (45•5%) were anaemic. Four patients only had totally normal red cells on the blood film; most commonly seen were moderate ( + +) anisocytosis, with mild ( +) macrocytosis, microcytosis and polychromasia, as described previously (Fleming et al., 1984). Six subjects had elliptocytosis not associated with anaemia. Fifty-one (25•5%) had sickle cell trait, with nine to 12 individuals in each of the five groups: two had Hb-AC (groups 1 and 5). Malaria, predominantly P.falciparum, was observed in 53 (26•5%) of subjects. There was only one significant difference in frequency of parasite density between the treatment groups; P.falciparum gametocytes were more frequent in groups 3 and 5 (to receive iron supplements) than in groups 2 and 4 (not to receive iron supplements) (Table 5) Mean±s.D. t' "' two (60•4%) with malaria were anaemic, compared to 59 (40•1 %) without parasitaemia""",
            ]
        ),
        reasoning="""Excerpt 1 discusses various comparisons made between treatment groups. Because these groups are being compared directly, this indicates that they are part of the same study. Excerpt two just explains the statistical significance test use. Excerpt 3 indicates the data transformations used for variables. Exceprt 4 discusses different haematological measurements take in the study, and how frequently different conditions were observed in the different groups.""",
        answer="""The excerpts provided indicate that the study conducted two experiments. Final Answer: 2.""",
    ),
]

COUNT_EXPERIMENTS_SHARED: dict[
    str, Union[OrdinalWord, DependentTransform[Union[int, Sized]]]
] = dict(
    ordinal=OrdinalWord(capitalize=True),
    maybe_plural_excerpts=plural_transform(
        key="paragraphs", singular_case="", plural_case="s"
    ),
)


def count_from_answer(answer: str) -> int:
    nums = extract_nums(answer)
    if not nums:
        log.warning("No number in final answer; expected count", answer=answer)
    return nums[-1] if nums else 0


COUNT_EXPERIMENTS_REASONING_STOP = ("\n\nHere's all",)


def make_count_experiments_prompt_func(num_shots: int) -> MultipartReasoningPrompt:
    def count_experiments_prompt(
        paragraphs: Sequence[str],
        helpfulness: Optional[str] = None,
        reasoning: Optional[str] = None,
    ) -> str:
        helpfulness  # ignored
        last_example: dict[
            str, Union[ValueTransform[Sequence[str]], str, StopSentinel]
        ] = dict(
            paragraphs=numbered_list(paragraphs),
            reasoning=reasoning if reasoning else stop("Excerpt 1"),
        )
        if reasoning:
            last_example["answer"] = stop("")
        shots = format_multi(
            COUNT_EXPERIMENTS_EXAMPLE_TEMPLATE,
            COUNT_EXPERIMENTS_EXAMPLES[:num_shots] + [last_example],
            COUNT_EXPERIMENTS_SHARED,
        )
        return "\n\n".join([COUNT_EXPERIMENTS_PREFACE] + list(shots))

    return count_experiments_prompt


def get_count_exps_reasoning(response: str) -> str:
    return "".join(
        ("Excerpt 1 ", get_part(response, "RCTs): ", "\nHere's all the information"))
    )
