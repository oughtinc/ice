from collections.abc import Sequence
from typing import cast

from ice.apis.openai import openai_complete
from ice.formatter.transform.dependent import CountWord
from ice.formatter.transform.dependent import plural_transform
from ice.paper import Paper
from ice.recipe import Recipe
from ice.recipe import recipe
from ice.recipes.experiments_and_arms.golds import get_ea_gs
from ice.recipes.experiments_and_arms.num_utils import strip_enumeration_prefix
from ice.recipes.experiments_and_arms.prompts.can_name_exps import (
    CAN_WE_NAME_EXPERIMENTS_BEST_CHOICE,
)
from ice.recipes.experiments_and_arms.prompts.can_name_exps import (
    CAN_WE_NAME_EXPERIMENTS_CHOICES,
)
from ice.recipes.experiments_and_arms.prompts.can_name_exps import (
    CAN_WE_NAME_EXPERIMENTS_REASONING_STOP,
)
from ice.recipes.experiments_and_arms.prompts.can_name_exps import (
    get_can_we_name_experiments_helpfulness,
)
from ice.recipes.experiments_and_arms.prompts.can_name_exps import (
    get_can_we_name_experiments_reasoning,
)
from ice.recipes.experiments_and_arms.prompts.can_name_exps import (
    make_can_we_name_experiments_prompt,
)
from ice.recipes.experiments_and_arms.prompts.name_exps import get_name_exps_reasoning
from ice.recipes.experiments_and_arms.prompts.name_exps import make_name_exps_from_count
from ice.recipes.experiments_and_arms.prompts.name_exps import (
    NAME_EXPERIMENTS_REASONING_STOP,
)
from ice.recipes.experiments_and_arms.prompts.passages_to_keep import (
    keep_most_helpful_paragraphs,
)
from ice.recipes.experiments_and_arms.prompts.quick_list import make_quick_list_prompt
from ice.recipes.experiments_and_arms.recipes.best_passages import (
    rate_helpfulness_with_reasoning,
)
from ice.recipes.experiments_and_arms.recipes.consensus import best_answer_by_consensus
from ice.recipes.experiments_and_arms.recipes.count_experiments import count_experiments
from ice.recipes.experiments_and_arms.recipes.reason_select_and_answer import (
    answer_with_best_reasoning,
)
from ice.recipes.experiments_and_arms.types import PassageWithReasoning
from ice.trace import Recorder
from ice.trace import recorder
from ice.trace import trace


async def first(exps: Sequence[PassageWithReasoning[str]]) -> PassageWithReasoning[str]:
    return exps[0]


def make_reduce_to_best_answer(num_experiments: int):
    async def reduce_to_best_answer(
        candidates: Sequence[PassageWithReasoning[str]],
    ) -> PassageWithReasoning[str]:
        answers = [c.final_answer for c in candidates if c.final_answer]
        question = f"""What {plural_transform("key", "was", "were").transform(num_experiments)} the {CountWord("key").transform(num_experiments)} experiment{plural_transform("key", "", "s").transform(num_experiments)} conducted in this paper?"""
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
async def best_paras_for_naming_experiments(paper: Paper):
    experiment_count, _ = await count_experiments(paper)
    assert experiment_count.final_answer is not None
    paragraphs = [str(p) for p in paper.nonempty_paragraphs()]
    passages_by_relevance = await rate_helpfulness_with_reasoning(
        paragraphs,
        make_can_we_name_experiments_prompt(experiment_count.final_answer),
        CAN_WE_NAME_EXPERIMENTS_CHOICES,
        CAN_WE_NAME_EXPERIMENTS_BEST_CHOICE,
        reasoning_stop=CAN_WE_NAME_EXPERIMENTS_REASONING_STOP,
        get_reasoning=get_can_we_name_experiments_reasoning,
        get_helpfulness=get_can_we_name_experiments_helpfulness,
        num_shots=3,
        passages_per_prompt=4,
        step=1,
    )

    paragraphs_to_keep = await keep_most_helpful_paragraphs(passages_by_relevance)
    return [p in paragraphs_to_keep for p in paragraphs], paragraphs


@trace
async def name_experiments(
    paper: Paper, record: Recorder = recorder
) -> tuple[Sequence[str], Sequence[str], Sequence[str], Sequence[str]]:
    """What were the experiments conducted in this paper?

    Args:
        paper (Paper): The paper in question.
        record (Recorder, optional): (recorder for tracing). Defaults to recorder.

    Returns:
        tuple[Sequence[str], Sequence[str]]: The gold standard experiments and the generated experiments.
    """
    gs = get_ea_gs(paper.document_id)
    if gs and gs.parsed_answer:
        gs_names = [exp.name for exp in gs.parsed_answer.experiments]
    else:
        gs_names = []
    experiment_count, _ = await count_experiments(paper)
    assert experiment_count.final_answer is not None

    paragraphs = paper.nonempty_paragraphs()
    passages_by_relevance = await rate_helpfulness_with_reasoning(
        [str(p) for p in paragraphs],
        make_can_we_name_experiments_prompt(experiment_count.final_answer),
        CAN_WE_NAME_EXPERIMENTS_CHOICES,
        CAN_WE_NAME_EXPERIMENTS_BEST_CHOICE,
        reasoning_stop=CAN_WE_NAME_EXPERIMENTS_REASONING_STOP,
        get_reasoning=get_can_we_name_experiments_reasoning,
        get_helpfulness=get_can_we_name_experiments_helpfulness,
        num_shots=3,
        passages_per_prompt=4,
        step=1,
    )

    paragraphs_to_keep = await keep_most_helpful_paragraphs(passages_by_relevance)

    experiment_names = await answer_with_best_reasoning(
        num_samples=10,  # TODO: Better sampling here
        selector=make_reduce_to_best_answer(
            num_experiments=experiment_count.final_answer
        ),
        # selector=first,
        texts=paragraphs_to_keep,
        # texts=count_paras,
        num_examples=2,
        reasoning_temperature=0.4,
        reasoning_stop=NAME_EXPERIMENTS_REASONING_STOP,
        prompt_func=make_name_exps_from_count(experiment_count.final_answer),
        get_reasoning=get_name_exps_reasoning,
        get_helpfulness=None,
        final_answer_processor=lambda resp: cast(str, resp["choices"][0]["text"]),
    )

    standardized_answer = await convert_answer_to_standardized_format(
        experiment_names.final_answer
    )

    assert experiment_names.final_answer is not None
    return (
        gs_names,
        [
            strip_enumeration_prefix(exp_name)
            for exp_name in standardized_answer.split("\n")
            if exp_name.strip()
        ]
        if standardized_answer
        else [],
        paragraphs_to_keep,
        [str(p) for p in paragraphs],
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


class NameExperiments(Recipe):
    async def run(self, paper: Paper):
        return await name_experiments(paper)


recipe.main(name_experiments)
