from collections.abc import Sequence
from typing import cast

from ice.apis.openai import openai_complete
from ice.paper import Paper
from ice.recipe import recipe
from ice.recipes.experiments_and_arms.num_utils import strip_enumeration_prefix
from ice.recipes.experiments_and_arms.prompts.can_name_arms import (
    CAN_WE_NAME_ARMS_BEST_CHOICE,
)
from ice.recipes.experiments_and_arms.prompts.can_name_arms import (
    CAN_WE_NAME_ARMS_CHOICES,
)
from ice.recipes.experiments_and_arms.prompts.can_name_arms import (
    CAN_WE_NAME_ARMS_REASONING_STOP,
)
from ice.recipes.experiments_and_arms.prompts.can_name_arms import (
    get_can_we_name_arms_helpfulness,
)
from ice.recipes.experiments_and_arms.prompts.can_name_arms import (
    get_can_we_name_arms_reasoning,
)
from ice.recipes.experiments_and_arms.prompts.can_name_arms import (
    make_can_we_name_arms_prompt,
)
from ice.recipes.experiments_and_arms.prompts.name_arms import get_name_arms_reasoning
from ice.recipes.experiments_and_arms.prompts.name_arms import make_name_arms_from_exps
from ice.recipes.experiments_and_arms.prompts.name_arms import NAME_ARMS_REASONING_STOP
from ice.recipes.experiments_and_arms.prompts.passages_to_keep import (
    keep_most_helpful_paragraphs,
)
from ice.recipes.experiments_and_arms.prompts.quick_list import make_quick_list_prompt
from ice.recipes.experiments_and_arms.recipes.best_passages import (
    rate_helpfulness_with_reasoning,
)
from ice.recipes.experiments_and_arms.recipes.consensus import best_answer_by_consensus
from ice.recipes.experiments_and_arms.recipes.reason_select_and_answer import (
    answer_with_best_reasoning,
)
from ice.recipes.experiments_and_arms.types import PassageWithReasoning
from ice.trace import Recorder
from ice.trace import recorder
from ice.trace import trace


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
    record: Recorder = recorder,
) -> Sequence[str]:
    """What were  the trial arms for this experiment?

    Args:
        paper (Paper): The paper in question.
        experiments (Sequence[str]): All the experiments in the paper.
        experiment_in_question (str): The experiment to identify the trial arms for.
        record (Recorder, optional): (recorder for tracing). Defaults to recorder.

    Returns:
        Sequence[str]: The trial arms for the `experiment_in_question`
    """
    paragraphs = paper.nonempty_paragraphs()
    passages_by_relevance = await rate_helpfulness_with_reasoning(
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

    paragraphs_to_keep = await keep_most_helpful_paragraphs(passages_by_relevance)

    arm_names = await answer_with_best_reasoning(
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

    final_answer: str = await convert_answer_to_standardized_format(
        arm_names.final_answer
    )

    return (
        [
            strip_enumeration_prefix(exp_name)
            for exp_name in final_answer.split("\n")
            if exp_name.strip()
        ]
        if final_answer
        else []
    )


@trace
async def convert_answer_to_standardized_format(answer: str) -> str:
    standardized_answer: str = (
        await openai_complete(
            prompt=make_quick_list_prompt(answer),
            stop="\n\nAnswer:",
        )
    )["choices"][0]["text"]
    return standardized_answer


recipe.main(name_arms)
