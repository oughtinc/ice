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
from ice.recipes.experiments_and_arms.prompts.utils import get_part
from ice.recipes.experiments_and_arms.types import MultipartReasoningPrompt

log = get_logger()

# TODO: WRITE PROMPTS ##

NAME_ARMS_PREFACE = """When evaluating a Randomized Controlled Trial, we should first identify its methodology; in particular, we should identify how different subgroups of participants were split into different trial arms, in order to receive different treatments or controls. We will look at a few paragraphs from different papers to identify the trial arms for specific experiments. Once we do this task, we will be able to draw a chart identifying, for each experiment, what the trial arms were. After that, we will look to identify how many participants were put into each arm, and how randomization was performed. Some of these excerpts may not be helpful, so we'll only pay attention to the excerpts that provide explicit information about what the trial arms (subgroups of participants) were for a specific experiment."""

NAME_ARMS_EXAMPLE_TEMPLATE = """
{ordinal}, consider the following excerpt{maybe_plural_excerpts} from a paper that conducted {experiment_count_word} experiment{maybe_plural_experiments}:

{paragraphs}

This paper discusses {experiment_count_word} experiment{maybe_plural_experiments}:

{experiments}

Let's focus on identifying the trial arms just for this experiment for now:

{experiment_in_question}

Let's think about what each excerpt tells us, if anything, about the trial arms (subgroups of participants) for that experiment: {reasoning}

In summary, the trial arms for this experiment in particular were:

{answer}
""".strip()


NAME_ARMS_EXAMPLES: list[dict[str, Union[ValueTransform[Sequence[str]], str, int]]] = [
    dict(
        paragraphs=numbered_list(
            [
                """This study was a 6-month, 2-arm cluster randomized controlled trial comparing a pre-school self-regulation program (PRSIST Program) with typical practice (control group). Fifty pre-school centers in metropolitan and regional areas of Australia were recruited to be broadly representative of population proportions for geography (84% metropolitan), socio-economic decile for their catchment area (M = 5.91, SD = 2.24, range = 1-10), and statutory quality assessment rating (i.e., 44% Exceeding, 48% Meeting, 4% Working Toward, 4% unrated against the National Quality Standard). Australia's early childhood education and care (ECEC) sector includes a range of pre-school provision (e.g., preschool for 4-5-year old children in the year before formal schooling, long-day care services from infant to age 5, family day care) that is delivered by not-for-profit, for-profit or state providers. While there is no state or national curriculum for the Australian ECEC sector, all pre-school services are required to follow the Australian Early Years Learning Framework, which outlines expected outcomes of children from birth to age 5. For this study, participating pre-schools: were structurally equivalent in terms of being long-day care services providing care to children aged 2-5 years, up to 5 days/week; were run by community or not-for-profit providers; and had at least one Bachelor-qualified educator (or government waiver).""",
                """Adherence to intervention participation thresholds was evaluated in terms of educators' completion of the online professional development modules and having engaged children in a minimum of three child activities per week. Engagement with optional program components (i.e., use of formative assessment tool, participation in monthly teleconference calls) was also captured. Educators' engagement in the online professional development was captured via log in and tracking functionality of the professional development modules. Of the 25 intervention centers, 20 services (80%) had at least one educator complete the professional development within the first 3 months of the intervention period (20% of the services had more than one educator complete the professional development during this time). Type and frequency of child activities each month was captured through a custom-designed activity sticker calendar, which was returned monthly to the research team. On average, six of the program's self-regulation activities were facilitated with children each week across the intervention period, ranging from none per week to 22 per week. Further, the charts indicated the suggested diversity of activities was met by most centers in most weeks, and certainly over the duration of the program (by centers who engaged with the child activities).""",
            ]
        ),
        reasoning="""Excerpt 1 identifies the two trial arms as (1) a pre-school self-regulation program (PRSIST Program) and (2) typical practice (control group). Ewxcerpt 2 discuss adherence to protocols but does not add any information about trial arms.""",
        answer=numbered_list(
            [
                "a pre-school self-regulation program (PRSIST Program)",
                "control (typical practice)",
            ]
        ),
        experiments=numbered_list(["the PRSIST program"]),
        experiment_in_question="the PRSIST program",
    ),
    dict(
        paragraphs=numbered_list(
            [
                """to the control group (column 2, rows 15 and 16), whereas for efficiency the observed increase is 46.67% (column 8, same rows). This large difference in efficiency can be also seen in Figure 8 , where the bottom of the post-treatment box of the mindfulness group has almost the same value than the top of the same box of the control group, i.e. after the intervention, approximately 75% of the subjects who practiced mindfulness were more efficient than 75% of the subjects who did not.""",
                """After performing the normality and homoscedasticity tests to determine the applicability of either parametric or nonparametric statistical tests, two mixed-model ANOVAs were carried out for each response variable 7 .""",
                """To avoid any differences in the ISEIS lessons taught to the subjects, all of them had the same professors and the same content taught at the same pace.""",
            ]
        ),
        reasoning="""Excerpt 1 discusses two arms, a mindfulness group and a control group. Excerpt 2 does not add any information about the arms. Excerpt 3 does not add any information about arms.""",
        answer=numbered_list(["mindfulness group", "control group"]),
        experiments=numbered_list(
            [
                "Baseline experiment",
                "1st internal replication",
                "2nd internal replication",
            ]
        ),
        experiment_in_question="2nd internal replication",
    ),
]

NAME_ARMS_SHARED: dict[
    str, Union[OrdinalWord, DependentTransform[Union[int, Sized]]]
] = dict(
    ordinal=OrdinalWord(capitalize=True, finally_case="Finally"),
    maybe_plural_excerpts=plural_transform(
        key="paragraphs", singular_case="", plural_case="s"
    ),
    experiment_count_word=CountWord("experiments"),
    maybe_plural_experiments=plural_transform(
        key="experiments", singular_case="", plural_case="s"
    ),
)


NAME_ARMS_REASONING_STOP = ("\n\nIn summary",)


def make_name_arms_from_exps(
    experiments: Sequence[str],
    experiment_in_question: str,
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
                experiments=numbered_list(experiments),
                experiment_in_question=experiment_in_question,
            )
            if reasoning:
                last_example["answer"] = stop("")
            shots = format_multi(
                NAME_ARMS_EXAMPLE_TEMPLATE,
                NAME_ARMS_EXAMPLES[:num_shots] + [last_example],
                NAME_ARMS_SHARED,
            )
            return "\n\n".join([NAME_ARMS_PREFACE] + list(shots))

        return name_experiments_prompt

    return make_name_experiments_prompt_func


def get_name_arms_reasoning(response: str) -> str:
    return "".join(("Excerpt 1", get_part(response, ": ", "\nIn summary")))
