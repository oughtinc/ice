from fvalues import F

from ice.recipe import recipe


def make_subquestion_prompt(question: str) -> str:
    return F(
        f"""Decompose the following question into 2-5 subquestions that would help you answer the question. Make the questions stand alone, so that they can be answered without the context of the original question.

Question: "{question}"
Subquestions:
-"""
    ).strip()


async def ask_subquestions(
    question: str = "What is the effect of creatine on cognition?",
):
    prompt = make_subquestion_prompt(question)
    subquestions_text = await recipe.agent().complete(prompt=prompt)
    subquestions = [line.strip("- ") for line in subquestions_text.split("\n")]
    return subquestions


recipe.main(ask_subquestions)
