import asyncio

from ice.agents.anthropic import ClaudeAgent
from ice.recipes.primer.subquestions import ask_subquestions
from ice.utils import map_async


def make_qa_prompt(question: str) -> str:
    return f"""Answer the following question:\nQuestion: "{question}"\nAnswer: """


async def answer(question: str) -> str:
    agent = ClaudeAgent()
    prompt = make_qa_prompt(question)
    answer = await agent.complete(prompt=prompt, max_tokens=256)
    return answer


async def answer_by_amplification(
    question: str = "What is the effect of creatine on cognition?",
):
    subquestions = await ask_subquestions(question=question)
    subanswers = await map_async(subquestions, answer)
    return list(zip(subquestions, subanswers))


# To run the async function in Python script

if __name__ == "__main__":
    question = "What is the effect of creatine on cognition?"
    answers = asyncio.run(answer_by_amplification(question))
    for subquestion, subanswer in answers:
        print(f"Subquestion: {subquestion}\nSubanswer: {subanswer}\n")
