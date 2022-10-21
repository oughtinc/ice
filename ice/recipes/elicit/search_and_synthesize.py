from ice.recipe import recipe
from ice.recipes.abstract_qa import Abstract
from ice.recipes.elicit.search import elicit_search
from ice.recipes.synthesize import synthesize
from ice.recipes.synthesize_compositional import synthesize_compositional


async def search_and_synthesize(
    question: str = "What is the effect of creatine on cognition?",
    compositional: bool = False,
):
    elicit_response = await elicit_search(question=question, num_papers=4)
    elicit_papers = list(elicit_response["papers"].values())

    abstracts = [
        Abstract(
            title=paper["title"],
            authors=paper["authors"],
            year=paper["year"],
            text=paper["unsegmentedAbstract"],
        )
        for paper in elicit_papers
    ]

    if compositional:
        synthesis = await synthesize_compositional(
            question=question, abstracts=abstracts
        )
    else:
        synthesis = await synthesize(question=question, abstracts=abstracts)

    return synthesis


recipe.main(search_and_synthesize)
