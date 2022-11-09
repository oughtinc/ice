from functools import partial
from itertools import chain
from ice.formatter.transform.value import numbered_list
from ice.metrics.gold_standards import GoldStandard
from typing import Iterable, Sequence
from ice.paper import Paper
from ice.recipes.experiments_and_arms.golds import get_ea_gs
#from ice.recipes.experiments_and_arms.recipes.name_experiments import (
#     NameExperiments,
#     best_paras_for_naming_experiments,
# )
from ice.recipes.experiments_and_arms.types import ExperimentsArms
from ice.recipes.meta.eval_paper_qa.eval_paper_qa import (
    cheating_few_shot_qa_baseline,
    cheating_qa_baseline,
    eval_method,
    few_shot_qa_with_support,
    paper_qa_baseline,
    search_qa_baseline,
)
from ice.recipe import recipe

from ice.recipes.meta.eval_paper_qa.types import PaperQaAnswer, PaperQaGoldStandard
from ice.recipes.meta.eval_paper_qa.utils import download_paper, download_papers


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
    paper = download_paper(gold.document_id)
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
    paper = download_paper(gold.document_id)
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


async def cheating_eval_experiments_qa_baseline():
    # Cheat by question-answering using gold standard excerpts
    method = partial(cheating_qa_baseline, enumerate_answer=True)
    return await eval_method(
        method=method,
        question_and_answer_func=experiments_questions_and_answers,
        split="validation",
        question_short_name="experiments_arms",
        get_gs=get_ea_gs,  # TODO: make native version
    )

async def search_eval_experiments_qa_baseline():
    # Test search recipes with a baseline generation method
    method = partial(
        search_qa_baseline,
        gold_support_func=experiments_gold_support_func,
    )
    return await eval_method(
        method=method,
        question_and_answer_func=experiments_questions_and_answers,#,experiments_questions_and_answers,
        split="validation",
        question_short_name="experiments_arms",
        get_gs=get_ea_gs,  # TODO: make native version
    )


def experiments_gold_support_func(
    document_id: str, consolidate: bool = False
) -> Sequence[PaperQaGoldStandard]:
    papers = [
        p
        for p in download_papers(
            split="validation", question_short_name="experiments_arms"
        )
        if p.document_id != document_id
    ]
    gss = [get_ea_gs(p.document_id) for p in papers]
    paper_gs = list(
        chain(
            *[
                experiments_questions_and_answers(gs, consolidate=consolidate)
                for gs in gss
                if gs
            ]
        )
    )
    return paper_gs


def arms_gold_support_func(
    document_id: str, consolidate: bool = False
) -> Sequence[PaperQaGoldStandard]:
    papers = [
        p
        for p in download_papers(
            split="validation", question_short_name="experiments_arms"
        )
        if p.document_id != document_id
    ]
    gss = [get_ea_gs(p.document_id) for p in papers]
    paper_gs = list(
        [arms_questions_and_answers(gs, consolidate=consolidate) for gs in gss if gs]
    )
    used_gs = []
    for paper in paper_gs:
        for gs in paper:
            # 1 per paper
            used_gs.append(gs)
            break

    return used_gs


async def cheating_eval_experiments_with_demonstrations():
    method = partial(
        cheating_few_shot_qa_baseline,
        enumerate_answer=True,
        gold_support_func=experiments_gold_support_func,
    )
    return await eval_method(
        method=method,
        question_and_answer_func=experiments_questions_and_answers,
        split="validation",
        question_short_name="experiments_arms",
        get_gs=get_ea_gs,
    )

def to_paragraphs(paper: Paper) -> Sequence[str]:
    return [str(p) for p in paper.paragraphs]

async def cheating_paragraph_eval_experiments_with_demonstrations():
    method = partial(
        cheating_few_shot_qa_baseline,
        enumerate_answer=True,
        gold_support_func=experiments_gold_support_func,
        paper_division_func=to_paragraphs
    )
    return await eval_method(
        method=method,
        question_and_answer_func=experiments_questions_and_answers,
        split="validation",
        question_short_name="experiments_arms",
        get_gs=get_ea_gs,
    )



async def cheating_eval_experiments_with_reasoning_demonstrations():
    method = partial(
        cheating_few_shot_qa_baseline,
        enumerate_answer=True,
        gold_support_func=partial(experiments_gold_support_func, consolidate=True),
        reasoning=True,
    )
    return await eval_method(
        method=method,
        question_and_answer_func=experiments_questions_and_answers,
        split="validation",
        question_short_name="experiments_arms",
        get_gs=get_ea_gs,
    )

async def cheating_paragraph_eval_experiments_with_reasoning_demonstrations():
    method = partial(
        cheating_few_shot_qa_baseline,
        enumerate_answer=True,
        gold_support_func=partial(experiments_gold_support_func, consolidate=True),
        paper_division_func=to_paragraphs,
        reasoning=True,
    )
    return await eval_method(
        method=method,
        question_and_answer_func=experiments_questions_and_answers,
        split="validation",
        question_short_name="experiments_arms",
        get_gs=get_ea_gs,
    )



async def cheating_eval_arms_with_reasoning_demonstrations():
    method = partial(
        cheating_few_shot_qa_baseline,
        enumerate_answer=True,
        gold_support_func=partial(arms_gold_support_func, consolidate=True),
        reasoning=True,
    )
    return await eval_method(
        method=method,
        question_and_answer_func=arms_questions_and_answers,
        split="validation",
        question_short_name="experiments_arms",
        get_gs=get_ea_gs,
    )


async def eval_experiments_qa_baseline():
    method = partial(paper_qa_baseline, enumerate_answer=True)
    return await eval_method(
        method=method,
        question_and_answer_func=experiments_questions_and_answers,
        split="validation",
        question_short_name="experiments_arms",
        get_gs=get_ea_gs,  # TODO: make native version
    )


async def non_cheating_experiments(paper: Paper, question: str, *args, **kwargs):
    paras_kept, all_paras = await best_paras_for_naming_experiments(paper=paper)
    answer = await few_shot_qa_with_support(
        paper=paper,
        question=question,
        support_labels=paras_kept,
        support_candidates=all_paras,
        enumerate_answer=True,
        gold_support_func=partial(experiments_gold_support_func, consolidate=True),
        reasoning=True,
    )
    return answer


async def eval_non_cheating_exps():
    return await eval_method(
        method=non_cheating_experiments,
        question_and_answer_func=experiments_questions_and_answers,
        split="validation",
        question_short_name="experiments_arms",
        get_gs=get_ea_gs,
    )


# recipe.main(eval_experiments_qa_baseline)
# recipe.main(eval_non_cheating_exps)
# recipe.main(cheating_eval_experiments_with_demonstrations)
# recipe.main(cheating_eval_experiments_with_reasoning_demonstrations)
# recipe.main(cheating_eval_arms_with_reasoning_demonstrations)
# recipe.main(cheating_paragraph_eval_experiments_with_demonstrations)
recipe.main(search_eval_experiments_qa_baseline)