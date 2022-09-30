
from ice.recipe import recipe
from ice.recipes.experiments_and_arms.prompts.quick_evaluate import get_grade, make_quick_eval_prompt
from ice.recipes.experiments_and_arms.types import ExperimentsArms
from ice.formatter.multi import format_multi
from ice.apis.openai import openai_complete




async def quick_evaluate(gs: ExperimentsArms, generated: ExperimentsArms) -> tuple[str, str]:
    prompt, stop_seq = make_quick_eval_prompt(gs, generated)
    response = (await openai_complete(prompt, stop=stop_seq))["choices"][0]["text"]
    return response, get_grade(response)


recipe.main(quick_evaluate)
