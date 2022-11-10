
from typing import Iterable
from ice.formatter.transform.value import numbered_list
from ice.metrics.gold_standards import GoldStandard, load_paper
from ice.recipes.experiments_and_arms.types import ExperimentsArms
from ice.recipes.meta.eval_paper_qa.types import PaperQaGoldStandard


def experiments_questions_and_answers(
    gold: GoldStandard[ExperimentsArms], consolidate: bool = False
) -> Iterable[PaperQaGoldStandard]:
    if not gold.parsed_answer:
        return
    experiments = gold.parsed_answer.experiments
    gold_answer = [f"{exp.name}: {exp.description}" for exp in experiments]
    if consolidate:
        gold_answer = (
            numbered_list(gold_answer).transform()
            + "\n\n"
            + f"({len(gold_answer)} experiment{'s' if len(gold_answer) > 1 else ''} in total)"
        )
    question = """Experiments are distinct from trial arms or groups; a single experiment might have multiple trial arms, like different interventions or controls. What experiment or experiments (aka trials, RCTs, studies) were conducted in this paper? Enumerate them, being mindful that there may just be one experiment or there could be more than one. Include the name and a brief description of each experiment."""
    gold_support = gold.quotes
    paper = load_paper(gold.document_id)
    yield PaperQaGoldStandard(
        paper=paper, question=question, gold_answer=gold_answer, gold_support=gold_support
    )


def arms_questions_and_answers(
    gold: GoldStandard[ExperimentsArms], consolidate: bool = False
) -> Iterable[PaperQaGoldStandard]:
    if not gold.parsed_answer:
        return
    experiments = gold.parsed_answer.experiments
    all_exps = numbered_list(
        [f"{exp.name}: {exp.description}" for exp in experiments], separator=" / "
    ).transform()
    paper = load_paper(gold.document_id)
    for experiment in experiments:
        gold_answer = [f"{arm.name}: {arm.description}" for arm in experiment.arms]
        if consolidate:
            gold_answer = (
                numbered_list(gold_answer).transform()
                + "\n\n"
                + f"{len(gold_answer)} arm{'s' if len(gold_answer) > 1 else ''} in total)"
            )
        if len(all_exps) > 1:
            question = f"""This paper studied multiple experiments: {all_exps}. For the {experiment.name} experiment specifically, what were the different trial arms (subgroups of participants)?""".strip()
        else:
            question = f"What were the different trial arms (subgroups of participants) in the {experiment.name} ({experiment.description}) experiment?"
        yield PaperQaGoldStandard(
            paper=paper, question=question, gold_answer=gold_answer, gold_support=gold.quotes
        )
