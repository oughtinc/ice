from ice.paper import Paper
from ice.recipe import Recipe, recipe
from ice.recipes.experiments_and_arms.recipes.name_experiments import name_experiments
from ice.recipes.experiments_and_arms.recipes.quick_evaluate import quick_evaluate
from ice.recipes.experiments_and_arms.types import ExperimentsArms, Experiment, Arm
from ice.recipes.experiments_and_arms.golds import get_ea_gs
from ice.recipes.experiment_arms import ExperimentArms
from ice.utils import map_async
from functools import partial
from ice.trace import recorder, trace


USE_GS = False

_ARMS_RECIPE: ExperimentArms | None = None


def arms_recipe() -> ExperimentArms:
    global _ARMS_RECIPE
    if not _ARMS_RECIPE:
        try:
            mode = recipe._mode
        except AttributeError:
            mode = "machine"
        mode = mode or "machine"
        _ARMS_RECIPE = ExperimentArms(mode=mode)
    return _ARMS_RECIPE


@trace
async def experiments_and_arms(paper: Paper, record=recorder):
    gs = get_ea_gs(paper.document_id)
    gs_exps, exps = await name_experiments(paper)

    if gs and gs.parsed_answer:
        gs_exps = [exp.name for exp in gs.parsed_answer.experiments]
    else:
        gs_exps = []

    arms = [([""], [""]) for _ in range(len(exps))]
    # async def run_arms(experiment: str):
    #     return await arms_recipe().run(paper, experiment)

    # arms = await map_async(exps, run_arms)
    result = ExperimentsArms(experiments=[
        Experiment(
            name=exp, description="", arms=[Arm(name="", description="") for a in arm]
        )
        for exp, arm in zip(exps, arms)
    ])
    gs_answer = gs.parsed_answer if gs and gs.parsed_answer else ExperimentsArms(experiments=[])

    evaluation, grade = await quick_evaluate(gs_answer, result)

    return grade, evaluation, gs_answer, result



class ExperimentsAndArms(Recipe):
    async def run(self, paper: Paper):
        global _ARMS_RECIPE
        _ARMS_RECIPE = ExperimentArms(mode=self.mode)
        return await experiments_and_arms(paper)
