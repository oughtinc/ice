from ice.recipe import recipe
from ice.recipes.primer.subquestions import ask_subquestions
from ice.utils import map_async

Question = str
Answer = str
Subs = list[dict[str, str]]


def render_background(subs: Subs) -> str:
    subs_text = "\n\n".join(f"Q: {q} A: {a}" for (q, a) in subs)
    return f"Here is relevant background information \n\n{subs_text}\n\n"


def make_qa_prompt(question: str, subs: Subs) -> str:
    background_text = render_background(subs)
    return f"""{background_text}Answer the following question using the background information provided above, wherever helpful:

Question: "{question}"
Answer: "
"""


def make_scenario_prompt_factored(scenario: str, subs: Subs) -> str:
    background_text = render_background(subs)
    return (
        f"""
        {background_text}
        scenario: "{scenario}"

You are presented with a challenging ethical scenario. Please provide a nuanced ethical and moral analysis. Consider the following while forming your response:

Break this down into 2-5 subquestions that are relevant to producing an ethically rounded response, evaluating from multiple viewpoints.
"""
    ).strip()


async def get_subs(question: str) -> Subs:
    subquestions = await ask_subquestions(question=question)
    subanswers = await map_async(subquestions, answer)
    return [{"Q": q, "A": a} for q, a in zip(subquestions, subanswers)]


async def answer(question: str, subs: Subs = [], engine: str = "chatgpt") -> str:
    """
    Generate an answer using subquestions as context
    """
    prompt = make_scenario_prompt_factored(question, subs=subs)
    answer = await recipe.agent(agent_name=engine).complete(
        prompt=prompt, stop='"', max_tokens=1000
    )
    return answer


async def answer_by_amplification(
    question: str = "Is it ethical to clone humans?", engine: str = "chatgpt"
):
    subs = await get_subs(question)
    response = await answer(question, subs=subs, engine=engine)
    subs = [{"Q": q, "A": a} for (q, a) in subs]
    return response, subs


recipe.main(answer_by_amplification)
