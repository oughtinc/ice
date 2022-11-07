from typing import cast
from urllib.parse import urljoin

import httpx

from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_random_exponential

from ice.agents.base import Agent
from ice.settings import settings

Vector = list[float]

URL = settings.OUGHT_INFERENCE_URL


class OughtInferenceAgent(Agent):
    def __init__(self, engine: str):
        self.url = urljoin(URL, engine)

    @retry(wait=wait_random_exponential(), stop=stop_after_attempt(3))
    async def relevance(
        self, *, question, context, verbose=False, default=None
    ) -> float:
        return (await self._post_json(dict(query=question, documents=[context])))[
            "results"
        ][0]["score"]

    async def _post_json(self, data: dict) -> dict:
        async with httpx.AsyncClient() as client:
            client.headers["x-api-key"] = settings.OUGHT_INFERENCE_API_KEY
            response = await client.post(self.url, json=data)
            response.raise_for_status()
        return response.json()


async def embed(
    query: str,
    *,
    endpoint: str = "paraphrase-mpnet",
) -> Vector:
    agent = OughtInferenceAgent(endpoint)
    result = await agent._post_json(dict(documents=[query]))
    return cast(Vector, result["embeddings"][0])
