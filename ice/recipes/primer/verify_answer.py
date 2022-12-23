from fvalues import F

from ice.recipe import recipe


def make_verification_prompt(question: str, answer: str) -> str:
    return F(
        f"""Consider this question: "{question}"

Potential answer: "{answer}"

Q: Is the potential answer above correct? Say "A: Yes" or "A: No".
A:"""
    )


async def verify_answer(question: str, answer: str) -> float:
    prompt = make_verification_prompt(question=question, answer=answer)
    choice_probs, _ = await recipe.agent().classify(
        prompt=prompt, choices=(" Yes", " No")
    )
    return choice_probs.get(" Yes", 0)


recipe.main(verify_answer)
