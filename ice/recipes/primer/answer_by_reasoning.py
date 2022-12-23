from fvalues import F

from ice.recipe import recipe


def generate_reasoning_prompt(question: str) -> str:
    return F(
        f"""Answer the following question:

Question: "{question}"
Answer: "Let's think step by step.
"""
    ).strip()


def generate_answer_prompt(question: str, reasoning: str) -> str:
    return F(
        f"""Answer the following question using the reasoning shown below:

Question: "{question}"
Reasoning: "{reasoning}"
Short answer: "
"""
    ).strip()


async def get_reasoning(question: str) -> str:
    reasoning_prompt = generate_reasoning_prompt(question)
    reasoning = await recipe.agent().complete(prompt=reasoning_prompt, stop='"')
    return reasoning


async def get_answer(question: str, reasoning: str) -> str:
    answer_prompt = generate_answer_prompt(question, reasoning)
    answer = await recipe.agent().complete(prompt=answer_prompt, stop='"')
    return answer


async def answer_by_reasoning(
    question: str = "What would happen if the average temperature in Northern California went up by 5 degrees Fahrenheit?",
) -> str:
    reasoning = await get_reasoning(question)
    answer = await get_answer(question, reasoning)
    return answer


recipe.main(answer_by_reasoning)
