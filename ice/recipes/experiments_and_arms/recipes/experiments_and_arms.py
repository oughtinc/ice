from typing import Sequence
from ice.paper import Paper
from ice.recipe import Recipe, recipe
from ice.recipes.experiments_and_arms.recipes.name_experiments import name_experiments
from ice.recipes.experiments_and_arms.recipes.name_arms import name_arms
from ice.recipes.experiments_and_arms.recipes.quick_evaluate import quick_evaluate
from ice.recipes.experiments_and_arms.types import ExperimentsArms, Experiment, Arm
from ice.recipes.experiments_and_arms.golds import get_ea_gs
from ice.recipes.experiment_arms import ExperimentArms
from ice.utils import map_async
from functools import partial
from ice.trace import recorder, trace


USE_GS = False


@trace
async def experiments_and_arms(paper: Paper, record=recorder):
    gs = get_ea_gs(paper.document_id)
    gs_exps, exps = await name_experiments(paper)

    if gs and gs.parsed_answer:
        gs_exps = [exp.name for exp in gs.parsed_answer.experiments]
    else:
        gs_exps = []

    # arms = [([""], [""]) for _ in range(len(exps))]
    async def run_arms(experiment_in_question: str) -> Sequence[str]:
        return await name_arms(paper=paper, experiments=exps, experiment_in_question=experiment_in_question)

    arms_by_exp = await map_async(exps, run_arms)
    result = ExperimentsArms(experiments=[
        Experiment(
            name=exp, description="", arms=[Arm(name=a, description="") for a in arm]
        )
        for exp, arm in zip(exps, arms_by_exp)
    ])
    gs_answer = gs.parsed_answer if gs and gs.parsed_answer else ExperimentsArms(experiments=[])

    evaluation, grade = await quick_evaluate(gs_answer, result)

    return grade, evaluation, gs_answer, result



class ExperimentsAndArms(Recipe):
    async def run(self, paper: Paper):
        return await experiments_and_arms(paper)
