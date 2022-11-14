from urllib.parse import urljoin

import httpx

from tenacity import retry
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_random_exponential

from ice.agents.base import Agent
from ice.settings import settings
from ice.cache import diskcache


class OughtInferenceAgent(Agent):
    def __init__(self, engine: str):
        self.url = urljoin(settings.OUGHT_INFERENCE_URL, engine)

    @retry(wait=wait_random_exponential(), stop=stop_after_attempt(3))
    async def relevance(
        self, *, question, context, verbose=False, default=None
    ) -> float:
        async with httpx.AsyncClient() as client:
            client.headers["x-api-key"] = settings.OUGHT_INFERENCE_API_KEY
            response = await client.post(
                self.url, json=dict(query=question, documents=[context])
            )
            response.raise_for_status()
        return response.json()["results"][0]["score"]

    @diskcache()
    @retry(wait=wait_random_exponential(), stop=stop_after_attempt(8))
    async def embeddings(self, documents: list[str]) -> list[list[float]]:
        print("Calling OughtInferenceAgent.embeddings", settings.OUGHT_INFERENCE_API_KEY, self.url)
        async with httpx.AsyncClient() as client:
            client.headers["x-api-key"] = settings.OUGHT_INFERENCE_API_KEY
            response = await client.post(self.url, json=dict(documents=documents))
            response.raise_for_status()
        return response.json()["embeddings"]
    
    def __repr__(self):
        return f"OughtInferenceAgent({self.url})"
