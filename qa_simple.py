from ice.recipe import recipe

def make_qa_prompt(question: str) -> str:
    return f"""Answer the following question:

Question: "{question}"
Answer: "
""".strip()

async def answer(question: str = "What is happening on 9/9/2022?"):
    prompt = make_qa_prompt(question)
    answer = (await recipe.agent().answer(prompt=prompt)).strip('" ')
    return answer

recipe.main(answer)