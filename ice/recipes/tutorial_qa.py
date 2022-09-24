from ice.recipe import Recipe


DEFAULT_CONTEXT = "We're running a hackathon on 9/9/2022 to decompose complex reasoning tasks into subtasks that are easier to automate & evaluate with language models. Our team is currently breaking down reasoning about the quality of evidence in randomized controlled trials into smaller tasks e.g. placebo, intervention adherence rate, blinding procedure, etc."

DEFAULT_QUESTION = "What is happening on 9/9/2022?"


def make_qa_prompt(context: str, question: str) -> str:
    return f"""
Background text: "{context}"

Answer the following question about the background text above:

Question: "{question}"
Answer: "
""".strip()


class QA(Recipe):
    async def run(
        self, context: str = DEFAULT_CONTEXT, question: str = DEFAULT_QUESTION
    ) -> str:
        prompt = make_qa_prompt(context, question)
        answer = (await self.agent().answer(prompt=prompt)).strip('" ')
        return answer
