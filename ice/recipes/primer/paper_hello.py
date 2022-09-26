from ice.paper import Paper
from ice.recipe import recipe


async def answer_for_paper(paper: Paper):
    return paper.paragraphs[0]


recipe.main(answer_for_paper)
