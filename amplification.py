from ice.recipe import recipe
from ice.recipes.primer.subquestions import ask_subquestions
from ice.utils import map_async
from functools import partial

Question = str
Answer = str
Subs = list[tuple[Question, Answer]]


def render_background(subs: Subs) -> str:
    subs_text = "\n\n".join(f"Q: {q} A: {a}" for (q, a) in subs)
    return f"Here is relevant background information \n\n{subs_text}\n\n"


# def make_qa_prompt(question: str, subs: Subs) -> str:
#     background_text = render_background(subs)
#     return f"""{background_text}Answer the following question using the background information provided above, wherever helpful:

# Question: "{question}"
# Answer: "
# """
def make_qa_prompt(question: str, subquestion: str) -> str:
    return F(
        f"""You are provided with an original question: {question}
        Based on this question, answer the following question:

Question: "{subquestion}"
Answer: "
"""
    ).strip()


async def sub_answer(question: str = "What is the effect of creatine on cognition?", subquestion: str = "What is creatine?", engine: str = "chatgpt") -> str:
    prompt = make_qa_prompt(question, subquestion)
    answer = await recipe.agent(agent_name=engine).complete(prompt=prompt, stop='"')
    return answer

def make_contextual_prompt(prompt: str, subs: Subs) -> str:
    background_text = render_background(subs)
    return f"""{background_text}

    {prompt}
Answer: "
"""


def make_inclusive_prompt(question: str, original_question: str, subs: Subs) -> str:
    background_text = render_background(subs)
    return f"""{background_text}Answer the following question using the background information provided above, wherever helpful:
    The purpose of answering this question is to help with answering this question: {original_question}
Question: "{question}"
Answer: "
"""


# async def get_subs(question: str) -> Subs:
#     subquestions = await ask_subquestions(question=question)
#     subanswers = await map_async(subquestions, answer)
#     return list(zip(subquestions, subanswers))

async def get_subs(
    question: str = "What is the effect of creatine on cognition?",
):
    subquestions = await ask_subquestions(question=question)
    subs_answer = partial(sub_answer, question=question)
    subanswers = await map_async(subquestions, subs_answer)
    return list(zip(subquestions, subanswers))

async def answer(
    prompt: str,
    subs: Subs = [],
    engine: str = "chatgpt",
) -> str:
    """
    Generate an answer using subquestions as context
    """
    prompt = make_contextual_prompt(prompt=prompt, subs=subs)
    answer = await recipe.agent(agent_name=engine).complete(prompt=prompt, stop='"')

    return answer


async def answer_by_amplification(
    prompt: str = "Is it ethical to clone humans?", engine: str = "chatgpt"
):
    subs = await get_subs(prompt)
    response = await answer(prompt, subs=subs, engine=engine)
    subs = [(q, a) for q, a in subs]
    return response, subs


recipe.main(answer_by_amplification)
