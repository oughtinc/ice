from typing import Sequence, TypeVar, cast
from ice.apis.openai import openai_complete
from ice.formatter.transform.dependent import CountWord, plural_transform
from ice.formatter.transform.value import numbered_list
from ice.paper import Paper
from ice.recipes.experiments_and_arms.golds import get_ea_gs
from ice.recipes.experiments_and_arms.prompts.can_name_arms import (
    CAN_WE_NAME_ARMS_BEST_CHOICE,
    CAN_WE_NAME_ARMS_CHOICES,
    CAN_WE_NAME_ARMS_REASONING_STOP,
    get_can_we_name_arms_helpfulness,
    get_can_we_name_arms_reasoning,
    make_can_we_name_arms_prompt,
)
from ice.recipes.experiments_and_arms.prompts.name_arms import (
    NAME_ARMS_REASONING_STOP,
    get_name_arms_reasoning,
    make_name_arms_from_exps,
)
from ice.recipes.experiments_and_arms.prompts.passages_to_keep import (
    most_helpful_paragraphs,
)
from ice.recipes.experiments_and_arms.prompts.quick_list import make_quick_list_prompt
from ice.recipes.experiments_and_arms.recipes.best_passages import rank_passages
from ice.recipes.experiments_and_arms.recipes.cluster import best_answer_by_clustering
from ice.recipes.experiments_and_arms.recipes.consensus import best_answer_by_consensus
from ice.recipes.experiments_and_arms.recipes.count_experiments import count_experiments
from ice.recipes.experiments_and_arms.recipes.reason_select_and_answer import (
    sample_reason_select_and_answer,
)
from ice.recipe import Recipe, recipe
from ice.recipes.experiments_and_arms.types import PassageWithReasoning
from ice.trace import recorder, trace
from ice.recipes.experiments_and_arms.num_utils import strip_enumeration_prefix


def make_reduce_to_best_answer(experiment_in_question: str):
    async def reduce_to_best_answer(
        candidates: Sequence[PassageWithReasoning[str]],
    ) -> PassageWithReasoning[str]:
        answers = [c.final_answer for c in candidates if c.final_answer]
        question = f"""What were the trial arms (subgroups of participants) conducted in the experiment: {experiment_in_question}"""
        return PassageWithReasoning(
            passage=candidates[0].passage,
            reasoning="",
            helpfulness="",
            final_answer=await (
                # best_answer_by_clustering(question=question, candidates=answers)
                best_answer_by_consensus(question=question, candidates=answers)
            ),
        )

    return reduce_to_best_answer


@trace
async def name_arms(
    paper: Paper,
    experiments: Sequence[str],
    experiment_in_question: str,
    record=recorder,
):
    paragraphs = paper.nonempty_paragraphs()
    passages_by_relevance = await rank_passages(
        [str(p) for p in paragraphs],
        make_can_we_name_arms_prompt(
            experiments=experiments, experiment_in_question=experiment_in_question
        ),
        CAN_WE_NAME_ARMS_CHOICES,
        CAN_WE_NAME_ARMS_BEST_CHOICE,
        reasoning_stop=CAN_WE_NAME_ARMS_REASONING_STOP,
        get_reasoning=get_can_we_name_arms_reasoning,
        get_helpfulness=get_can_we_name_arms_helpfulness,
        num_shots=3,
        passages_per_prompt=4,
        step=1,
    )

    paragraphs_to_keep = await most_helpful_paragraphs(passages_by_relevance)

    arm_names = await sample_reason_select_and_answer(
        num_samples=6,  # TODO: Better sampling here
        selector=make_reduce_to_best_answer(experiment_in_question),
        # selector=first,
        texts=paragraphs_to_keep,
        # texts=count_paras,
        num_examples=2,
        reasoning_temperature=0.4,
        reasoning_stop=NAME_ARMS_REASONING_STOP,
        prompt_func=make_name_arms_from_exps(
            experiments=experiments, experiment_in_question=experiment_in_question
        ),
        get_reasoning=get_name_arms_reasoning,
        get_helpfulness=None,
        final_answer_processor=lambda resp: cast(str, resp["choices"][0]["text"]),
    )

    assert arm_names.final_answer is not None

    final_answer: str = (await openai_complete(make_quick_list_prompt(arm_names.final_answer), stop="\n\nAnswer"))["choices"][0]["text"]

    return (
        [
            strip_enumeration_prefix(exp_name)
            for exp_name in final_answer.split("\n")
            if exp_name.strip()
        ]
        if final_answer
        else []
    )




recipe.main(name_arms)
