import json

from collections.abc import Sequence
from functools import partial

from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.paper import Paper
from ice.recipe import Recipe
from ice.recipe import recipe
from ice.recipes.experiment_arms import ExperimentArms
from ice.recipes.experiments_and_arms.golds import get_ea_gs
from ice.recipes.experiments_and_arms.recipes.name_arms import name_arms
from ice.recipes.experiments_and_arms.recipes.name_experiments import name_experiments
from ice.recipes.experiments_and_arms.recipes.quick_evaluate import quick_evaluate
from ice.recipes.experiments_and_arms.types import Arm
from ice.recipes.experiments_and_arms.types import Experiment
from ice.recipes.experiments_and_arms.types import ExperimentsArms
from ice.trace import recorder
from ice.trace import trace
from ice.utils import map_async


USE_GS = False


@trace
async def experiments_and_arms(
    paper: Paper, record=recorder
) -> tuple[str, str, ExperimentsArms, ExperimentsArms]:
    """What were the experiments performed in this paper, and for each experiment, what were the trial arms?

    Args:
        paper (Paper): Paper to evaluate.
        record (Recorder, optional): (recorder for tracing). Defaults to recorder.

    Returns:
        tuple[str, str, ExperimentsArms, ExperimentsArms]: The quick-eval grade, the explanation for that grade, the gold standard answer, and the generated answer.
    """
    gs = get_ea_gs(paper.document_id)
    gs_exps, exps = await name_experiments(paper)

    if gs and gs.parsed_answer:
        gs_exps = [exp.name for exp in gs.parsed_answer.experiments]
    else:
        gs_exps = []

    async def run_arms(experiment_in_question: str) -> Sequence[str]:
        return await name_arms(
            paper=paper, experiments=exps, experiment_in_question=experiment_in_question
        )

    arms_by_exp = await map_async(exps, run_arms)
    result = ExperimentsArms(
        experiments=[
            Experiment(
                name=exp,
                description="",
                arms=[Arm(name=a, description="") for a in arm],
            )
            for exp, arm in zip(exps, arms_by_exp)
        ]
    )
    gs_answer = (
        gs.parsed_answer if gs and gs.parsed_answer else ExperimentsArms(experiments=[])
    )

    evaluation, grade = await quick_evaluate(gs_answer, result)

    return grade, evaluation, gs_answer, result


class ExperimentsAndArms(Recipe):
    async def run(self, paper: Paper):
        """Wrapped experiments and arms recipe for evaluation script.

        Args:
            paper (Paper): Paper to evaluate.
        """
        grade, evaluation, _, result = await experiments_and_arms(paper)
        self.maybe_add_to_results(
            [
                RecipeResult(
                    question_short_name="experiments_arms",
                    document_id=paper.document_id,
                    experiment="",
                    excerpts=[],
                    answer=json.dumps(
                        result.dict()
                        | dict(autoeval_grade=grade, autoeval_reasoning=evaluation)
                    ),
                    result=result,
                )
            ]
        )
