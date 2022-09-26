
from ice.recipe import recipe
from ice.utils import map_async
from subquestions import ask_subquestions


def make_qa_prompt(question: str) -> str:
    return f"""Answer the following question:

Question: "{question}"
Answer: "
""".strip()


async def answer(question: str) -> str:
    prompt = make_qa_prompt(question)
    answer = (await recipe.agent().answer(prompt=prompt, multiline=False)).strip('" ')
    return answer


async def answer_by_amplification(question: str = "What is the effect of creatine on cognition?"):
        subquestions = await ask_subquestions(question=question)
        subanswers = await map_async(subquestions, answer)
        return list(zip(subquestions, subanswers))

recipe.main(answer_by_amplification)
