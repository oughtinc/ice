from typing import Sequence
from urllib.parse import urljoin
from ice.paper import Paper
from structlog import get_logger

from ice.recipe import recipe
from ice.recipes.elicit.common import send_elicit_request
import httpx

log = get_logger()


def make_request_body(
    query: str, num_papers: int = 4, page: int = 0, filters: dict | None = None
) -> dict:
    """
    Make the request body for the Elicit search endpoint.
    """
    if filters is None:
        filters = {}
    return dict(
        query=query,
        start=page * num_papers,
        stop=(page + 1) * num_papers,
        qaColumns=[],
        filters=filters,
    )


async def get_elicit_backend() -> str:
    BACKEND_URL = "https://elicit.org/api/backend"
    async with httpx.AsyncClient() as client:
        response = await client.get(BACKEND_URL)
        # Response is plain text, e.g. "https://prod.elicit.org/elicit-red/lit-review"
        response.raise_for_status()
        return response.text


def elicit_results_to_papers(elicit_results: dict) -> Sequence[Paper]:
    return [
        Paper.from_elicit_result(paper) for paper in elicit_results["papers"].values()
    ]


async def elicit_paper_search(question: str, num_papers: int = 4, page: int = 0, full_text: bool = True) -> Sequence[Paper]:
    return elicit_results_to_papers(
        await elicit_search(question, num_papers, page, full_text)
    )


async def elicit_search(
    question: str = "What is the effect of creatine on cognition?",
    num_papers: int = 4,
    page: int = 0,
    has_pdf_filter: bool = False,
    backend: str | None = None,
):
    """
    Search Elicit for papers related to a question.
    """

    backend = backend or await get_elicit_backend()

    endpoint = backend.rstrip("/") + "/lit-review"

    log.info(f"Searching Elicit for query: {question}, endpoint: {endpoint}")

    filters = dict(has_pdf=has_pdf_filter)

    request_body = make_request_body(
        query=question, num_papers=num_papers, page=page, filters=filters
    )

    response = send_elicit_request(
        request_body=request_body,
        endpoint=endpoint,
    )
    return response


recipe.main(elicit_search)
