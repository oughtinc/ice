from ice.recipe import recipe


def eval_python(expression: str) -> str:
    try:
        result = eval(expression)
    except Exception as e:
        result = f"Error: {e}"
    return str(result)


async def answer_by_computation(question: str):
    return eval_python(question)


recipe.main(answer_by_computation)
