from collections.abc import Callable
from collections.abc import Sequence
from collections.abc import Sized
from typing import Optional
from typing import Union

from structlog.stdlib import get_logger

from ice.formatter.multi import format_multi
from ice.formatter.multi import stop
from ice.formatter.multi import StopSentinel
from ice.formatter.transform.dependent import CountWord
from ice.formatter.transform.dependent import DependentTransform
from ice.formatter.transform.dependent import plural_transform
from ice.formatter.transform.positional import OrdinalWord
from ice.formatter.transform.value import numbered_list
from ice.formatter.transform.value import ValueTransform
from ice.recipes.experiments_and_arms.num_utils import extract_nums
from ice.recipes.experiments_and_arms.prompts.utils import get_part
from ice.recipes.experiments_and_arms.types import MultipartReasoningPrompt

log = get_logger()

# TODO: WRITE PROMPTS ##

NAME_EXPERIMENTS_PREFACE = """Some research papers cover just one experiment, while others cover multiple experiments. Experiments are distinct from trial arms or groups; a single experiment might have multiple trial arms, like different interventions or controls. Let's look at some excerpts from research papers covering different numbers of experiments and try to identify what those experiments were, being careful to not confuse experiments with trial arms.""".strip()

NAME_EXPERIMENTS_EXAMPLE_TEMPLATE = """
{ordinal}, consider the following excerpt{maybe_plural_excerpts} from a paper that conducted {experiments_count_word_or_just_one} experiment{maybe_plural_experiments}:

{paragraphs}

Let's think about what each excerpt tells us, if anything, about what {that_or_those} experiment{maybe_plural_experiments} {was_or_were}: {reasoning}

In summary, the {experiments_count_word} experiment{maybe_plural_experiments} {was_or_were}:

{answer}
""".strip()


NAME_EXPERIMENTS_EXAMPLES: list[
    dict[str, Union[ValueTransform[Sequence[str]], str, int]]
] = [
    dict(
        paragraphs=numbered_list(
            [
                "Contrary to expectations, participants in the park walking group reported an increase in fatigue at the end of the afternoon (d = -0.22) and the relaxation group experienced lower restoration in the evening compared to baseline (d = -0.18). In the evening the relaxation group experienced lower levels of fatigue (d = 0.25) than before the intervention. Across all time points of the working day, recovery experiences and outcomes in the week after the intervention were fairly similar to levels before the intervention in the three groups with average effect sizes around zero.",
                "After the intervention period the park walking group reported slightly lower levels of enjoyment of their lunch breaks (d = -0.38). The relaxation group experienced somewhat higher levels of detachment (d = 0.20) than before the intervention period. The control group's recovery experiences during lunch breaks were the same as before (d = -0.04). Concerning well-being outcomes, only the park walking group reported a positive change in restoration (d = 0.23) after lunch compared to baseline. All other changes after the lunch break were trivial in terms of effect sizes. In afternoons and evenings there were only three meaningful changes regarding well-being.",
                "The research plan for the RCT´s has been approved by the Ethical Committee of the Tampere Region, Finland. Data collection was divided into two phases to optimize our scarce material and personnel resources. The first RCT took place in spring (starting in week 18) and the second identical RCT in fall 2014 (starting in week 35). Thus, the second RCT in fall was a replication of the RCT in spring. Each RCT lasted five working weeks, two of which were the intervention period.",
                "There were three significant interaction terms of group x time, namely for detachment and enjoyment of the lunch break and for fatigue at the end of the afternoon (Table III ). The interaction effect for relaxation was marginally significant. The nature of these interactions will become clear in the following detailed description of the changes across time within the three groups.",
            ]
        ),
        reasoning="""Excerpt 1 discusses three groups, but does not distinguish between different experiments. Excerpt 2 also discusses two groups, a park walking group and a relaxation group, but the discussion suggests they belong to the same experiment. Excerpt 2 discusses two RCTs, one that took place in spring, and a second, which took place in fall 2014. These RCTs are separate experiments. Excerpt 4 discusses the three groups again but does not provide more information about the number of experiments.""",
        answer=numbered_list(["a spring RCT", "a fall 2014 RCT"]),
        experiments_count=2,
    ),
    dict(
        paragraphs=numbered_list(
            [
                "Patients were evaluated at baseline, 8 hours after the first administration of the study drug (tolvaptan or placebo), and on days 2, 3, 4, 11, 18, 25, 30, and 37 . Study drugs were withheld after day 30, and the effect of discontinuation of the study drug was assessed on day 37.",
                "The present study was conducted primarily in the outpatient setting, without mandated fluid restriction or a change in the patient's medication regimen, such as use of diuretics, to treat the patient's primary disease. Tolvaptan was superior to placebo with respect to several measures, including the change in the average daily AUC for serum sodium concentrations from baseline to day 4 and from baseline to day 30, the mean serum sodium concentration at each visit, the time to normalized serum sodium concentrations, the percentage of patients with serum sodium concentrations that were normal on day 4 and on day 30, and the categorical change in the serum sodium concentration from baseline to day 4 and from baseline to day 30. Tolvaptan was superior to placebo from the first observation point (8 hours) after administration of the first dose until the last treatment day (day 30) in patients with either mild or marked hyponatremia and among patients with hyponatremia from all major causes. During the 7-day follow-up period, serum sodium concentrations reverted to degrees of hyponatremia that were equivalent to those associated with the use of placebo, indicating that the aquaretic effect of tolvaptan (excretion of electrolyte-free water) was required to maintain normal sodium concentrations in patients with chronic hyponatremia.",
                "Patients were ineligible if they had clinically evident hypovolemic hyponatremia (a state in which normal plasma sodium concentrations could be reestablished through the restoration of plasma volume).",
                "Hyponatremia occurs in 15 to 20% of hospitalized patients and constitutes a common serum electrolyte abnormality. 22  Hyponatremia is reported to be an independent predictor of complications and death in patients with heart disease, 23,24 cirrhosis, 6 or neurologic disorders.",
            ]
        ),
        reasoning="""Excerpt 1 discusses two trial arms (tolvaptan and placebo). Because this paper studied one experiment, we can surmise that it was a study of tolvaptan. Excerpt 2 more information about the study. Excerpt 3 discusses exclusion criteria for participants. Expert 4 provides information about hyponatremia.""",
        answer=numbered_list(["a tolvaptan study"]),
        experiments_count=1,
    ),
]

NAME_EXPERIMENTS_SHARED: dict[
    str, Union[OrdinalWord, DependentTransform[Union[int, Sized]]]
] = dict(
    ordinal=OrdinalWord(capitalize=True, finally_case="Finally"),
    maybe_plural_excerpts=plural_transform(
        key="paragraphs", singular_case="", plural_case="s"
    ),
    experiments_count_word_or_just_one=CountWord("experiments_count", {1: "just one"}),
    maybe_plural_experiments=plural_transform(
        key="experiments_count", singular_case="", plural_case="s"
    ),
    that_or_those=plural_transform(
        key="experiments_count", singular_case="that", plural_case="those"
    ),
    was_or_were=plural_transform(
        key="experiments_count", singular_case="was", plural_case="were"
    ),
    experiments_count_word=CountWord(key="experiments_count"),
)


def count_from_answer(answer: str) -> int:
    nums = extract_nums(answer)
    if not nums:
        log.warning("No number in final answer; expected count", answer=answer)
    return nums[-1] if nums else 0


NAME_EXPERIMENTS_REASONING_STOP = ("\n\nIn summary",)


def make_name_exps_from_count(
    experiments_count: int,
) -> Callable[[int], MultipartReasoningPrompt]:
    def make_name_experiments_prompt_func(num_shots: int) -> MultipartReasoningPrompt:
        def name_experiments_prompt(
            paragraphs: Sequence[str],
            helpfulness: Optional[str] = None,
            reasoning: Optional[str] = None,
        ) -> str:
            helpfulness  # ignored
            last_example: dict[
                str, Union[ValueTransform[Sequence[str]], str, StopSentinel, int]
            ] = dict(
                paragraphs=numbered_list(paragraphs),
                reasoning=reasoning if reasoning else stop("Excerpt 1"),
                experiments_count=experiments_count,
            )
            if reasoning:
                last_example["answer"] = stop("")
            shots = format_multi(
                NAME_EXPERIMENTS_EXAMPLE_TEMPLATE,
                NAME_EXPERIMENTS_EXAMPLES[:num_shots] + [last_example],
                NAME_EXPERIMENTS_SHARED,
            )
            return "\n\n".join([NAME_EXPERIMENTS_PREFACE] + list(shots))

        return name_experiments_prompt

    return make_name_experiments_prompt_func


def get_name_exps_reasoning(response: str) -> str:
    return "".join(("Excerpt 1", get_part(response, ": ", "\nIn summary")))
