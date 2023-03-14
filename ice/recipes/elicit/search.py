from typing import Optional

import httpx
from structlog import get_logger

from ice.recipe import recipe
from ice.recipes.elicit.common import send_elicit_request

log = get_logger()


def make_request_body(
    query: str, num_papers: int = 4, page: int = 0, filters: Optional[dict] = None
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


async def elicit_search(
    question: str = "What is the effect of creatine on cognition?",
    num_papers: int = 4,
    page: int = 0,
    has_pdf_filter: bool = False,
    backend: Optional[str] = None,
    filters: Optional[dict] = None,
):
    """
    Search Elicit for papers related to a question.
    """

    backend = backend or await get_elicit_backend()

    endpoint = backend.rstrip("/") + "/lit-review"

    log.info(f"Searching Elicit for query: {question}, endpoint: {endpoint}")

    filters = filters or {}
    if has_pdf_filter:
        filters["has_pdf"] = True

    request_body = make_request_body(
        query=question, num_papers=num_papers, page=page, filters=filters
    )

    response = send_elicit_request(
        request_body=request_body,
        endpoint=endpoint,
    )
    return response


recipe.main(elicit_search)
