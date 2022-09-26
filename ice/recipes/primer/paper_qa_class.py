
from ice.recipe import recipe
from ice.paper import Paper, Paragraph

def make_prompt(paragraph: Paragraph, question: str) -> str:
    return f"""
Here is a paragraph from a research paper: "{paragraph}"

Question: Does this paragraph answer the question '{question}'? Say Yes or No.
Answer:""".strip()

async def classify_paragraph(paragraph: Paragraph, question: str) -> float:
    choice_probs, _ = await recipe.agent().classify(
        prompt=make_prompt(paragraph, question),
        choices=(" Yes", " No"),
    )
    return choice_probs.get(" Yes", 0.0)

async def answer_for_paper(paper: Paper, question: str = "What was the study population?"):
    paragraph = paper.paragraphs[0]
    return await classify_paragraph(paragraph, question)

recipe.main(answer_for_paper)
