from ice.recipes.primer.amplify_one.utils import *

async def get_subs(question: str) -> Subs:
    subquestions = await ask_subquestions(question=question)
    subanswers = await map_async(subquestions, answer)
    return list(zip(subquestions, subanswers))

async def answer(question: str, subs: Subs = []) -> str:
    prompt = make_qa_prompt(question, subs=subs)
    answer = (await recipe.agent().answer(prompt=prompt, multiline=False)).strip('" ')
    return answer

async def answer_by_amplification(question: str = "What is the effect of creatine on cognition?"):
    subs = await get_subs(question)
    response = await answer(question=question, subs=subs)
    return response

recipe.main(answer_by_amplification)
