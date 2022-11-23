from collections.abc import Mapping
from typing import Union

import httpx

from httpx import Response
from httpx import TimeoutException
from structlog.stdlib import get_logger
from tenacity import retry
from tenacity.retry import retry_any
from tenacity.retry import retry_if_exception
from tenacity.retry import retry_if_exception_type
from tenacity.wait import wait_random_exponential

from ice.cache import diskcache
from ice.settings import settings
from ice.trace import recorder
from ice.trace import trace
from aiolimiter import AsyncLimiter

log = get_logger()

limiter = AsyncLimiter(5)

class RateLimitError(Exception):
    def __init__(self, response: httpx.Response):
        self.response = response
        try:
            message = response.json()["error"]["message"]
        except Exception:
            message = response.text[:100]
        super().__init__(message)


def log_attempt_number(retry_state):
    if retry_state.attempt_number > 1:
        exception = retry_state.outcome.exception()
        exception_name = exception.__class__.__name__
        exception_message = str(exception)
        OPENAI_ORG_ID = settings.OPENAI_ORG_ID
        log.warning(
            f"Retrying ({exception_name}: {exception_message}): "
            f"Attempt #{retry_state.attempt_number} ({OPENAI_ORG_ID = })..."
        )


RETRYABLE_STATUS_CODES = {408, 429, 502, 503, 504}
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
}
if settings.OPENAI_ORG_ID:
    OPENAI_DEFAULT_HEADERS["OpenAI-Organization"] = settings.OPENAI_ORG_ID


def is_retryable_HttpError(e: BaseException) -> bool:
    return (
        isinstance(e, httpx.HTTPStatusError)
        and e.response.status_code in RETRYABLE_STATUS_CODES
    )


class TooLongRequestError(ValueError):
    def __init__(self, prompt: str = "", detail: str = ""):
        self.prompt = prompt
        self.detail = detail
        super().__init__(self.detail)


def raise_if_too_long_error(prompt: object, response: Response) -> None:
    # Raise something more specific than
    # a generic status error if we have exceeded
    # an OpenAI model's context window
    if not isinstance(prompt, str) or response.status_code != 400:
        return None
    try:
        body = response.json()
    except Exception:
        return None
    if not isinstance(body, dict):
        return None
    message = body.get("error", dict).get("message", "")
    if not isinstance(message, str):
        return None
    # This is a bit fragile, but since OpenAI can
    # return 400s for other reasons, checking
    # the message seems like the only real
    # way to tell.
    if "maximum context length" not in message:
        return None
    raise TooLongRequestError(prompt=prompt, detail=message)


@diskcache()
@retry(
    retry=retry_any(
        retry_if_exception(is_retryable_HttpError),
        retry_if_exception_type(TimeoutException),
        retry_if_exception_type(RateLimitError),
    ),
    wait=wait_random_exponential(min=1),
    after=log_attempt_number,
)
async def _post(
    endpoint: str, json: dict, timeout: float | None = None, cache_id: int = 0
) -> dict | TooLongRequestError:
    """Send a POST request to the OpenAI API and return the JSON response."""
    cache_id  # unused

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OPENAI_BASE_URL}/{endpoint}",
            json=json,
            headers=OPENAI_DEFAULT_HEADERS,
            timeout=timeout,
        )
        if response.status_code == 429:
            raise RateLimitError(response)
        try:
            raise_if_too_long_error(prompt=json.get("prompt"), response=response)
        except TooLongRequestError as tlre:
            # Hack alert: Don't raise here so this gets cached
            return tlre
        response.raise_for_status()
        return response.json()


# TODO: support more model types for conversion


def get_davinci_equivalent_tokens(response: dict) -> int:
    return (response.get("usage") or dict()).get("total_tokens", 0)


@trace
async def openai_complete(
    prompt: str,
    stop: str | None = "\n",
    top_p: float = 1,
    temperature: float = 0,
    model: str = "text-davinci-002",
    max_tokens: int = 256,
    logprobs: int | None = None,
    logit_bias: Mapping[str, int | float] | None = None,
    n: int = 1,
    echo: bool = False,
    cache_id: int = 0,  # for repeated non-deterministic sampling using caching
    record=recorder,
) -> dict:
    """Send a completion request to the OpenAI API and return the JSON response."""
    #model = "text-ada-001"

    #log.info("Sending completion request to OpenAI API", model=model)
    params = {
        "prompt": prompt,
        "stop": stop,
        "top_p": top_p,
        "temperature": temperature,
        "model": model,
        "echo": echo,
        "max_tokens": max_tokens,
        "logprobs": logprobs,
        "n": n,
    }
    if logit_bias:
        params["logit_bias"] = logit_bias  # type: ignore[assignment]

    response = await _post("completions", json=params, cache_id=cache_id)
    if isinstance(response, TooLongRequestError):
        raise response
    record(davinci_equivalent_tokens=get_davinci_equivalent_tokens(response))
    return response

@diskcache()
async def openai_embeddings(
    input: Union[str, list[str]],
    model: str = "ada-test-v2",
) -> Union[list[float], list[list[float]]]:
    """Send a embeddings request to the OpenAI API and return the JSON response."""
    async with limiter:
        log.info("Calling OpenAI embeddings API...")
        response = await _post(
            "embeddings",
            json={
                "input": input if isinstance(input, list) else [input],
                "model": model,
            },
        )

        if not response:
            raise ValueError("OpenAI API returned an empty response.")
        
        if isinstance(input, str):
            return response['data'][0]['embedding']
        
        return [response['data'][i]['embedding'] for i in range(len(input))]