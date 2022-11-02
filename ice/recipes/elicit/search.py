from ice.recipe import recipe
from ice.recipes.elicit.common import send_elicit_request

# TODO: Dynamically consult https://elicit.org/api/backend
ELICIT_SEARCH_ENDPOINT = "https://prod.elicit.org/elicit-red/lit-review"


def make_request_body(
    query: str, num_papers: int = 4, filters: dict | None = None
) -> dict:
    """
    Make the request body for the Elicit search endpoint.
    """
    if filters is None:
        filters = {}
    return dict(
        query=query,
        start=0,
        stop=num_papers,
        qaColumns=[],
        filters=filters,
    )


async def elicit_search(
    question: str = "What is the effect of creatine on cognition?",
    num_papers: int = 4,
):
    """
    Search Elicit for papers related to a question.
    """
    filters = None
    # filters = dict(
    #     has_pdf=True,
    #     study_types=["RCT"] if rct_only else [],
    # )
    request_body = make_request_body(
        query=question, num_papers=num_papers, filters=filters
    )
    response = send_elicit_request(
        request_body=request_body,
        endpoint=ELICIT_SEARCH_ENDPOINT,
    )
    return response


recipe.main(elicit_search)
