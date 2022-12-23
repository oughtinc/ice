from fvalues import F

from ice.recipe import recipe


def make_computation_choice_prompt(question: str) -> str:
    return F(
        f"""You've been asked to answer the question "{question}".

You have access to a Python interpreter.

Enter an expression that will help you answer the question.
>>>"""
    )


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


async def eval_selective(question: str):
    expression = await choose_computation(question)
    result = eval_python(expression)
    return (expression, result)


recipe.main(eval_selective)
