from collections.abc import Callable
from collections.abc import Iterable
from functools import partial
from itertools import islice
from typing import Type

from ice.formatter.transform.value import numbered_list
from ice.metrics.gold_standards import generate_papers_and_golds
from ice.metrics.gold_standards import GoldStandard
from ice.metrics.gold_standards import ParsedGoldStandardType
from ice.paper import Paper
from ice.recipes.consort_flow.types import ConsortFlow
from ice.recipes.experiments_and_arms.types import ExperimentsArms
from ice.recipes.meta.eval_paper_qa.types import PaperQaGoldStandard


def generate_paper_qa_gold_standards(
    split: str,
    gold_standard_type: Type[ParsedGoldStandardType],
    question_and_answer_generator: Callable[
        [Paper, GoldStandard[ParsedGoldStandardType]],
        Iterable[PaperQaGoldStandard],
    ],
) -> Iterable[PaperQaGoldStandard]:
    for paper, gold in generate_papers_and_golds(split, gold_standard_type):
        yield from question_and_answer_generator(paper, gold)


def experiments_questions_and_answers(
    paper: Paper, gold: GoldStandard[ExperimentsArms], consolidate: bool = False
) -> Iterable[PaperQaGoldStandard]:
    if not gold.parsed_answer:
        return
    experiments = gold.parsed_answer.experiments
    gold_answer = [f"{exp.name}: {exp.description}" for exp in experiments]
    short_gold_answer = [exp.name for exp in experiments]
    if consolidate:
        gold_answer = (
            numbered_list(gold_answer).transform()
            + "\n\n"
            + f"({len(gold_answer)} experiment{'s' if len(gold_answer) > 1 else ''} in total)"
        )
        short_gold_answer = numbered_list(short_gold_answer, separator=", ").transform()

    question = """Experiments are distinct from trial arms or groups; a single experiment might have multiple trial arms, like different interventions or controls. What experiment or experiments (aka trials, RCTs, studies) were conducted in this paper? Enumerate them, being mindful that there may just be one experiment or there could be more than one. Include the name and a brief description of each experiment."""
    gold_support = gold.quotes
    yield PaperQaGoldStandard(
        paper=paper,
        question=question,
        gold_answer=gold_answer,
        short_gold_answer=short_gold_answer,
        gold_support=gold_support,
    )


def generate_experiments_qas_lst(split: str):
    yield from generate_paper_qa_gold_standards(
        split, ExperimentsArms, experiments_questions_and_answers
    )


def only_10_generate_experiments_qas_lst(split: str):
    yield from islice(
        generate_paper_qa_gold_standards(
            split, ExperimentsArms, experiments_questions_and_answers
        ),
        10,
    )


def generate_experiments_qas_str(split: str):
    yield from generate_paper_qa_gold_standards(
        split,
        ExperimentsArms,
        partial(experiments_questions_and_answers, consolidate=True),
    )


def arms_questions_and_answers(
    paper: Paper, gold: GoldStandard[ExperimentsArms], consolidate: bool = False
) -> Iterable[PaperQaGoldStandard]:
    if not gold.parsed_answer:
        return
    experiments = gold.parsed_answer.experiments
    all_exps = numbered_list(
        [f"{exp.name}: {exp.description}" for exp in experiments], separator=" / "
    ).transform()
    for experiment in experiments:
        gold_answer = [f"{arm.name}: {arm.description}" for arm in experiment.arms]
        short_gold_answer = [arm.name for arm in experiment.arms]
        if consolidate:
            gold_answer = (
                numbered_list(gold_answer).transform()
                + "\n\n"
                + f"({len(gold_answer)} arm{'s' if len(gold_answer) > 1 else ''} in total)"
            )
            short_gold_answer = numbered_list(
                short_gold_answer, separator=", "
            ).transform()
        if len(experiments) > 1:
            question = f"""This paper studied multiple experiments: {all_exps}. For the {experiment.name} experiment specifically, what were the different trial arms (subgroups of participants)?""".strip()
        else:
            question = f"What were the different trial arms (subgroups of participants) in the {experiment.name} ({experiment.description}) experiment?"
        yield PaperQaGoldStandard(
            paper=paper,
            question=question,
            gold_answer=gold_answer,
            short_gold_answer=short_gold_answer,
            gold_support=gold.quotes,
        )


def generate_arms_qas_lst(split: str):
    yield from generate_paper_qa_gold_standards(
        split, ExperimentsArms, arms_questions_and_answers
    )


def generate_arms_qas_str(split: str):
    yield from generate_paper_qa_gold_standards(
        split,
        ExperimentsArms,
        partial(arms_questions_and_answers, consolidate=True),
    )


def adherence_questions_and_answers(
    paper: Paper, gold: GoldStandard[ConsortFlow]
) -> Iterable[PaperQaGoldStandard]:
    if not gold.parsed_answer:
        return
    experiments = gold.parsed_answer.experiments
    for experiment in experiments:
        arms = experiment.arms
        if not arms:
            return
        for arm in arms:
            EXPLANATION = "Adherence describes how many participants selected for an intervention actually received it. Attrition describes how many of the initial sample dropped out of the study or were otherwise not available to be included in the final analysis. Compliance describes how well participants in the intervention complied with its protocol."
            question = f"""{EXPLANATION} For the {arm.name} arm of the {experiment.name} ({experiment.description}) experiment specifically, what does the paper say about the adherence, attrition, or compliance rate (say 'not mentioned' if it is not mentioned)?"""
            adherence = arm.received
            if not adherence:
                continue
            gold_answer = (
                adherence if isinstance(adherence, str) else adherence.description
            )
            if not gold_answer:
                continue
            yield PaperQaGoldStandard(
                paper=paper,
                question=question,
                gold_answer=gold_answer,
                short_gold_answer=gold_answer,
                gold_support=[] if isinstance(adherence, str) else adherence.quotes,
            )


def generate_adherence_qas(split: str):
    yield from generate_paper_qa_gold_standards(
        split, ConsortFlow, adherence_questions_and_answers
    )
