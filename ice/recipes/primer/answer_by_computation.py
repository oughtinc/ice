from fvalues import F

from ice.recipe import recipe


def make_computation_choice_prompt(question: str) -> str:
    return F(
        f"""You've been asked to answer the question "{question}".

You have access to a Python interpreter.

Enter an expression that will help you answer the question.
>>>"""
    )


def make_compute_qa_prompt(question: str, expression: str, result: str) -> str:
    return F(
        f"""A recording of a Python interpreter session:

>>> {expression}: {result}

Answer the following question, using the Python session if helpful:

Question: "{question}"
Answer: "
"""
    ).strip()


def eval_python(expression: str) -> str:
    try:
        result = eval(expression)
    except Exception as e:
        result = F(f"Error: {e}")
    return str(result)


async def choose_computation(question: str) -> str:
    prompt = make_computation_choice_prompt(question)
    answer = await recipe.agent().complete(prompt=prompt, stop='"')
    return answer


async def answer_by_computation(question: str):
    expression = await choose_computation(question)
    result = eval_python(expression)
    prompt = make_compute_qa_prompt(question, expression, result)
    answer = await recipe.agent().complete(prompt=prompt, stop='"')
    return answer


recipe.main(answer_by_computation)
