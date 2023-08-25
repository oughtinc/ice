from ice.recipe import recipe
from ice.recipes.primer.subquestions import ask_subquestions
from ice.utils import map_async

Question = str
Answer = str
Subs = list[tuple[Question, Answer]]


def render_background(subs: Subs) -> str:
    subs_text = "\n\n".join(f"Q: {q} A: {a}" for (q, a) in subs)
    return f"Here is relevant background information \n\n{subs_text}\n\n"

def make_qa_prompt(question: str, subs: Subs) -> str:
    background_text = render_background(subs)
    return f"""{background_text}Answer the following question using the background information provided above, wherever helpful:

Question: "{question}"
Answer: "
"""

async def get_subs(question: str) -> Subs:
    subquestions = await ask_subquestions(question=question)
    subanswers= await map_async(subquestions, answer)
    return list(zip(subquestions, subanswers))

async def answer(question: str, subs: Subs = [], engine: str="chatgpt") -> str:
    """
    Generate an answer using subquestions as context
    """
    prompt = make_qa_prompt(question=question, subs=subs)
    answer = await recipe.agent(agent_name=engine).complete(prompt=prompt, stop='"')
    return answer

async def answer_by_amplification(question: str, engine: str="chatgpt"):
    subs = await get_subs(question)
    response = await answer(question, subs=subs, engine=engine)
    subs = [{"Q" :q, "A": a} for (q, a) in subs]
    return response, subs

recipe.main(answer_by_amplification)
