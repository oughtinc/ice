from collections.abc import Sequence

from ice.formatter.multi import format_multi
from ice.formatter.multi import stop
from ice.formatter.transform.dependent import plural_transform
from ice.formatter.transform.positional import OrdinalWord
from ice.formatter.transform.value import numbered_list
from ice.recipes.experiments_and_arms.prompts.utils import get_part
from ice.recipes.experiments_and_arms.types import Arm
from ice.recipes.experiments_and_arms.types import Experiment
from ice.recipes.experiments_and_arms.types import ExperimentsArms
from ice.recipes.experiments_and_arms.types import Sample

SCHRIER: dict[str, ExperimentsArms] = {
    "gold_standard": ExperimentsArms(
        experiments=[
            Experiment(
                name="SALT-1",
                description="multicenter, randomized, double-blind, placebo-controlled trial of tolvaptan for hyponatremia",
                arms=[
                    Arm(
                        name="tolvaptan",
                        description="15mg tablet of oral tolvaptan daily, dose increased if necessary",
                        sample=Sample(size=102, stage="randomized"),
                    ),
                    Arm(
                        name="placebo",
                        description="tablet matching the tolvaptan tablet",
                        sample=Sample(size=103, stage="randomized"),
                    ),
                ],
            ),
            Experiment(
                name="SALT-2",
                description="multicenter, randomized, double-blind, placebo-controlled trial of tolvaptan for hyponatremia",
                arms=[
                    Arm(
                        name="tolvaptan",
                        description="15mg tablet of oral tolvaptan daily, dose increased if necessary",
                        sample=Sample(size=123, stage="randomized"),
                    ),
                    Arm(
                        name="placebo",
                        description="tablet matching the tolvaptan tablet",
                        sample=Sample(size=120, stage="randomized"),
                    ),
                ],
            ),
        ]
    ),
    "computed": ExperimentsArms(
        experiments=[
            Experiment(
                name="a study of tolvaptan",
                description="",
                arms=[
                    Arm(name="Tolvaptan", description="Placebo", sample=None),
                    Arm(
                        name='The "Tolvaptan" trial arm was the group of patients who were given the tolvaptan drug as part of the study. The intervention for this group was that they were given the tolvaptan drug for 4 days and the dose could be increased according to a regimen designed for slow correction of serum sodium concentrations.',
                        description='The "Placebo" trial arm was set up to receive a matching placebo once daily for up to 30 days. The placebo was given in the morning in either an inpatient or outpatient setting as an adjunct to the patient\'s standard therapy. Fluid restriction was not mandatory according to the study protocol. Treatment of hyponatremia with demeclocycline, lithium chloride, or urea was not permitted.',
                        sample=None,
                    ),
                ],
            ),
            Experiment(
                name="a study of the effect of discontinuation of the study drug",
                description="",
                arms=[
                    Arm(
                        name="Tolvaptan group", description="Placebo group", sample=None
                    ),
                    Arm(
                        name="The Tolvaptan group received the study drug while the Placebo group did not. The study drug was given in increasing doses over 4 days until the patient's serum sodium concentration reached 135 mmol per liter or more. If the serum sodium concentration remained below 136 mmol per liter and had increased by less than 5 mmol per liter during the prior 24 hours, the dose was increased. If the serum sodium concentration rose above 145 mmol per liter or increased at too great a rate (by more than 12 mmol per liter during 24 hours or by more than 8 mmol per liter during 8 hours on the first day of therapy), the investigator either withheld or decreased the next dose or increased the patient's fluid intake.",
                        description="The Placebo group was given a placebo for the first 30 days and then had the study drug withheld on day 30. The effect of discontinuation of the study drug was assessed on day 37.",
                        sample=None,
                    ),
                ],
            ),
        ]
    ),
}

HAUGEN: dict[str, ExperimentsArms] = {
    "gold_standard": ExperimentsArms(
        experiments=[
            Experiment(
                name="Surgical Safety Checklist (SSC) experiment",
                description="a stepped wedge cluster RCT to examine the effect of the SSC on in-hospital complications",
                arms=[
                    Arm(
                        name="preintervention cases",
                        description="surgical cases from before the checklist was implemented for a surgical specialty",
                        sample=Sample(size=2212, stage="randomized"),
                    ),
                    Arm(
                        name="postintervention cases",
                        description="surgical cases from after the checklist was implemented for a surgical specialty",
                        sample=Sample(size=3083, stage="randomized"),
                    ),
                ],
            )
        ]
    ),
    "computed": ExperimentsArms(
        experiments=[
            Experiment(
                name="a study of the WHO SSC",
                description="",
                arms=[
                    Arm(
                        name="Cardiothoracic surgery",
                        description="Neurosurgery",
                        sample=None,
                    ),
                    Arm(
                        name='The Cardiothoracic surgery trial arm was one of 5 trial arms in the experiment described as a study of the WHO SSC. The other trial arms were Neurosurgery, Orthopedic surgery, General surgery, and Urologic surgery. The intervention in the Cardiothoracic surgery trial arm was the implementation of the WHO Surgical Safety Checklist (SSC). The SSC consisted of 20 items and was performed at 3 critical steps of the surgical procedure: the "sign in" before induction of anesthesia, the "time out" before start of surgery, and the "sign out" before the head surgeon left the operating room. The SSC was introduced in all specialties/hospitals while using an educational program with standardized lectures and information materials.',
                        description='The "Neurosurgery" trial arm in the experiment described as a study of the WHO SSC was a cluster randomized controlled trial of the SSC. The intervention was sequentially rolled out in a random order until all 5 clusters-cardiothoracic, neurosurgery, orthopedic, general, and urologic surgery had received the Checklist. Data were prospectively recorded in control and intervention stages during a 10-month period in 2009-2010.',
                        sample=None,
                    ),
                ],
            )
        ]
    ),
}


def to_exps(result: ExperimentsArms) -> Sequence[str]:
    ret_val: list[str] = []
    for exp in result.experiments:
        if exp.description:
            ret_val.append(f"{exp.name}: {exp.description}")
        else:
            ret_val.append(exp.name)
    return ret_val


def display_result(result: ExperimentsArms, as_gs: bool) -> str:
    lines: list[str] = []
    for exp in result.experiments:
        lines.append("Experiment:")
        lines.append(f"{exp.name}: {exp.description}" if as_gs else exp.name)
        for arm in exp.arms:
            lines.append("Arms for this experiment:")
            lines.append(f"\t{arm.name}: {exp.description}" if as_gs else arm.name)
        lines.append("\n")
    return "\n".join(lines).strip()


EXAMPLES = [
    dict(
        gs_exps=numbered_list(to_exps(SCHRIER["gold_standard"])),
        gen_exps=numbered_list(to_exps(SCHRIER["computed"])),
        gs_exps_and_arms=display_result(SCHRIER["gold_standard"], as_gs=True),
        gen_exps_and_arms=display_result(SCHRIER["computed"], as_gs=False),
        differences="The generated answer and the gold standard both have two experiments, so they agree on the number. The model identified that one of these experiments studied tolvaptan, which is correct, but it identified the other experiment as studying 'discontinuation' of the drug, which does not appear on the gold standard. The model did correctly identify that each of the experiments had a placebo arm and a treatment arm.",
        grade="C",
    ),
    dict(
        gs_exps=numbered_list(to_exps(HAUGEN["gold_standard"])),
        gen_exps=numbered_list(to_exps(HAUGEN["computed"])),
        gs_exps_and_arms=display_result(HAUGEN["gold_standard"], as_gs=True),
        gen_exps_and_arms=display_result(HAUGEN["computed"], as_gs=False),
        differences="The generated answer and the gold standard both have one experiment. While the gold standard spells out the abbrevation, the generated answer does not. This is an extremely minor difference, so we should ignore it. The model's descriptions of the trial arms for this study, however, seem substantially incorrect: the gold standard identifies the arms as a postintervention and a preintervention group, while the model's outputs mention cardiothoracic surgery and then a long discussion, which does not even appear to be a specific arm (this output seems like the wrong shape).",
        grade="F",
    ),
]

SHARED_PROMPT_PARTS = dict(
    ordinal_word=OrdinalWord(capitalize=True),
    maybe_plural_gs_exp=plural_transform("gs_exps", "", "s"),
    maybe_plural_gen_exp=plural_transform("gen_exps", "", "s"),
)

EXPERIMENTS_EXAMPLE = """{ordinal_word}, consider the following gold standard, which describes the experiment{maybe_plural_gs_exp} conducted in a study:

{gs_exps_and_arms}

The machine learning model generated the following experiment{maybe_plural_gen_exp}:

{gen_exps_and_arms}

Explain the major differences. Ignore differences in formatting, or uses of abbreviations, or other minor differences. The model's outputs will generally not be as detailed as the gold standards, but you should not reduce scores for this unless the model's outputs are actually incorrect.

{differences}

On an A-F scale, where A is the best, and F is the worst, the model scored: {grade}"""

PREAMBLE = """Let's compare some of the generations from the machine learning model to our labeled gold standards. We're interested in knowing how well the model's results approximate the gold standards, so we'll ignore minor differences. The gold standards will include additional descriptions, which we are not using the model to generate. These additional descriptions are here only to provide context to help us better grade the model's outputs. Use the following grading scale:

A: Substantially correct in all respects
B: Agree on the number of outputs and the main thrust of their meanings, but with small differences.
C: Agree on the number of outputs, but disagree on some of them, while agreeing on others.
D: Disagree on the number of outputs or on the nature of all of them, but with similar themes.
F: Wild disagreement; not remotely close."""


def make_quick_eval_prompt(
    gs: ExperimentsArms, result: ExperimentsArms
) -> tuple[str, tuple[str, ...]]:
    last_example = dict(
        gs_exps=numbered_list(to_exps(gs)),
        gen_exps=numbered_list(to_exps(result)),
        gs_exps_and_arms=display_result(gs, as_gs=True),
        gen_exps_and_arms=display_result(result, as_gs=False),
        differences=stop(""),
    )
    parts = [PREAMBLE] + list(
        format_multi(
            EXPERIMENTS_EXAMPLE, EXAMPLES + [last_example], SHARED_PROMPT_PARTS  # type: ignore[arg-type]
        )
    )
    stop_seq = OrdinalWord(capitalize=True).transform(len(EXAMPLES), len(EXAMPLES) + 1)
    return "\n\n".join(parts), ("\n" + stop_seq,)


def get_grade(response: str) -> str:
    return get_part(response, "the model scored:", "NOTHING_LEFT")
