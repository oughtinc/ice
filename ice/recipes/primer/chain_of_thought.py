from fvalues import F

from ice.recipe import recipe


def make_chain_of_thought_prompt(question: str, answer_prefix: str = "") -> str:
    return F(
        f"""Answer the following question:

Question: "{question}"
Answer: "{answer_prefix}
"""
    ).strip()


async def chain_of_thought(
    question: str = "What would happen if the average temperature in Northern California went up by 5 degrees Fahrenheit?",
    answer_prefix: str = "Let's think step by step.",
) -> str:
    prompt = make_chain_of_thought_prompt(question, answer_prefix)
    answer = await recipe.agent().complete(prompt=prompt, stop='"')
    return answer


recipe.main(chain_of_thought)
