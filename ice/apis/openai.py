import httpx

from httpx import TimeoutException
from structlog.stdlib import get_logger
from tenacity import retry
from tenacity.retry import retry_any
from tenacity.retry import retry_if_exception
from tenacity.retry import retry_if_exception_type
from tenacity.wait import wait_random_exponential

from ice.cache import diskcache
from ice.settings import settings

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


@retry(
    retry=retry_any(
        retry_if_exception(is_retryable_HttpError),
        retry_if_exception_type(TimeoutException),
        retry_if_exception_type(RateLimitError),
    ),
    wait=wait_random_exponential(min=1),
    after=log_attempt_number,
)
async def _post(endpoint: str, json: dict, timeout: float | None = None) -> dict:
    """Send a POST request to the OpenAI API and return the JSON response."""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OPENAI_BASE_URL}/{endpoint}",
            json=json,
            headers=OPENAI_DEFAULT_HEADERS,
            timeout=timeout,
        )
        if response.status_code == 429:
            raise RateLimitError(response)
        response.raise_for_status()
        return response.json()


@diskcache()
async def openai_complete(
    prompt: str,
    stop: str | None = "\n",
    top_p: float = 1,
    temperature: float = 0,
    model: str = "text-davinci-002",
    max_tokens: int = 256,
    logprobs: int | None = None,
    n: int = 1,
    echo: bool = False,
    cache_id: int = 0,  # for repeated non-deterministic sampling using caching
) -> dict:
    """Send a completion request to the OpenAI API and return the JSON response."""
    cache_id  # unused
    return await _post(
        "completions",
        json={
            "prompt": prompt,
            "stop": stop,
            "top_p": top_p,
            "temperature": temperature,
            "model": model,
            "max_tokens": max_tokens,
            "logprobs": logprobs,
            "n": n,
            "echo": echo,
        },
    )
