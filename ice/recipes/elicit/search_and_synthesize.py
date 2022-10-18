from ice.recipe import recipe
from ice.recipes.elicit.search import elicit_search
from ice.recipes.elicit.synthesize import Abstract
from ice.recipes.elicit.synthesize import synthesize


async def search_and_synthesize(
    question: str = "What is the effect of creatine on cognition?",
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

    synthesis = await synthesize(question=question, abstracts=abstracts)

    return synthesis


recipe.main(search_and_synthesize)
