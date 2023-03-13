from itertools import product
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

from ice.metrics.base import Metric
from ice.metrics.base import Sample
from ice.settings import settings
from ice.utils import map_async


class NubiaRequest(BaseModel):
    ref: str
    hyp: str


class NubiaResponse(BaseModel):
    nubia_score: float
    semantic_relation: float
    contradiction: float
    irrelevancy: float
    logical_agreement: float
    grammar_ref: float
    grammar_hyp: float


NUBIA_URL = urljoin(settings.OUGHT_INFERENCE_URL, "/nubia/")


async def _single_nubia(sample: Sample) -> list[NubiaResponse]:
    samples = list(product(sample.left, sample.right))

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=20, read=20, write=10, pool=30)
    ) as client:
        client.headers["x-api-key"] = settings.OUGHT_INFERENCE_API_KEY

        async def single_response(inputs: tuple[str, str]) -> NubiaResponse:
            hyp, ref = inputs
            response = await client.post(
                NUBIA_URL, json=NubiaRequest(ref=ref, hyp=hyp).dict()
            )
            return NubiaResponse.parse_obj(response.json())

        responses = await map_async(samples, single_response)

        return responses


class Nubia(Metric):
    name = "Nubia"

    async def compute(self, sample: list[Sample]) -> list[list[NubiaResponse]]:
        return await map_async(sample, _single_nubia)
