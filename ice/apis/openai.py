from collections.abc import Mapping
from typing import Optional
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
from ice.trace import add_fields
from ice.trace import trace

log = get_logger()


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


def make_headers() -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
    }
    if settings.OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = settings.OPENAI_ORG_ID
    return headers


RETRYABLE_STATUS_CODES = {408, 429, 502, 503, 504}
OPENAI_BASE_URL = "https://api.openai.com/v1"


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
    endpoint: str, json: dict, timeout: Optional[float] = None, cache_id: int = 0
) -> Union[dict, TooLongRequestError]:
    """Send a POST request to the OpenAI API and return the JSON response."""
    cache_id  # unused

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OPENAI_BASE_URL}/{endpoint}",
            json=json,
            headers=make_headers(),
            timeout=timeout or 60,
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


def extract_total_tokens(response: dict) -> int:
    return response.get("usage", {}).get("total_tokens", 0)


@trace
async def openai_complete(
    prompt: str,
    stop: Optional[str] = "\n",
    top_p: float = 1,
    temperature: float = 0,
    model: str = "gpt-3.5-turbo-instruct",
    max_tokens: int = 256,
    logprobs: Optional[int] = None,
    logit_bias: Optional[Mapping[str, Union[int, float]]] = None,
    n: int = 1,
    echo: bool = False,
    cache_id: int = 0,  # for repeated non-deterministic sampling using caching
) -> dict:
    """Send a completion request to the OpenAI API and return the JSON response."""
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
    add_fields(davinci_equivalent_tokens=extract_total_tokens(response))
    return response


@trace
async def openai_chatcomplete(
    messages: list[dict[str, str]],
    stop: Optional[str] = "\n",
    top_p: float = 1,
    temperature: float = 0,
    model: str = "gpt-3.5-turbo",
    max_tokens: int = 256,
    logit_bias: Optional[Mapping[str, Union[int, float]]] = None,
    n: int = 1,
    cache_id: int = 0,  # for repeated non-deterministic sampling using caching
) -> dict:
    """Send a completion request to the OpenAI API and return the JSON response."""
    params = {
        "messages": messages,
        "stop": stop,
        "top_p": top_p,
        "temperature": temperature,
        "model": model,
        "max_tokens": max_tokens,
        "n": n,
    }
    if logit_bias:
        params["logit_bias"] = logit_bias  # type: ignore[assignment]
    response = await _post("chat/completions", json=params, cache_id=cache_id)
    if isinstance(response, TooLongRequestError):
        raise response
    add_fields(total_tokens=extract_total_tokens(response))
    return response


@trace
async def openai_embedding(
    input: Union[str, list[str]],
    model: str = "text-embedding-ada-002",
    cache_id: int = 0,  # for repeated non-deterministic sampling using caching
) -> dict:
    """Send an embedding request to the OpenAI API and return the JSON response."""
    params = {
        "input": input,
        "model": model,
    }
    response = await _post("embeddings", json=params, cache_id=cache_id)
    if isinstance(response, TooLongRequestError):
        raise response
    add_fields(total_tokens=extract_total_tokens(response))
    return response
