from ice.recipe import Recipe
from ice.utils import map_async


def make_subquestion_prompt(question: str) -> str:
    return f"""Decompose the following question into 2-5 subquestions that would help you answer the question. Make the questions stand alone, so that they can be answered without the context of the original question.

Question: "{question}"
Subquestions:
-""".strip()


class Subquestions(Recipe):
    async def run(self, question: str = "What is the effect of creatine on cognition?"):
        prompt = make_subquestion_prompt(question)
        subquestions_text = await self.agent().answer(
            prompt=prompt, multiline=True, max_tokens=100
        )
        subquestions = [line.strip("- ") for line in subquestions_text.split("\n")]
        return subquestions


Question = str
Answer = str
Subs = list[tuple[Question, Answer]]


def render_background(subs: Subs) -> str:
    if not subs:
        return ""
    subs_text = "\n\n".join(f"Q: {q}\nA: {a}" for (q, a) in subs)
    return f"Here is relevant background information:\n\n{subs_text}\n\n"


def make_qa_prompt(question: str, subs: Subs) -> str:
    background_text = render_background(subs)
    return f"""{background_text}Answer the following question, using the background information above where helpful:

Question: "{question}"
Answer: "
""".strip()


class AmplifiedQA(Recipe):
    async def run(
        self,
        question: str = "What is the effect of creatine on cognition?",
        depth: int = 1,
    ):
        subs = await self.get_subs(question, depth - 1) if depth > 0 else []
        prompt = make_qa_prompt(question, subs=subs)
        answer = (await self.agent().answer(prompt=prompt, max_tokens=100)).strip('" ')
        return answer

    async def get_subs(self, question: str, depth: int) -> Subs:
        subquestions = await Subquestions().run(question=question)
        subanswers = await map_async(subquestions, lambda q: self.run(q, depth))
        return list(zip(subquestions, subanswers))
