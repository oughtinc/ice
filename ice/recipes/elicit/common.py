import json
from functools import reduce
from pathlib import Path

import httpx
from dotenv import dotenv_values
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_random_exponential

from ice.cache import diskcache
from ice.settings import settings
from ice.utils import deep_merge

script_dir = Path(__file__).parent
root_dir = script_dir.parent.parent.parent
config = dotenv_values(root_dir / ".env")


@diskcache()
# try 5 times, because sometimes preview apps take a while to start responding again after they have an issue
@retry(stop=stop_after_attempt(5), wait=wait_random_exponential(2), reraise=True)
def send_elicit_request(*, request_body, endpoint: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.ELICIT_AUTH_TOKEN}",
    }
    chunks = []

    with httpx.stream(
        "POST",
        endpoint,
        json=request_body,
        headers=headers,
        timeout=40,
    ) as r:
        r.raise_for_status()
        for chunk in r.iter_text():
            chunks.append(chunk)

    joined = "".join(chunks)
    split_on_newlines = joined.split("\n")
    as_json = [json.loads(line) for line in split_on_newlines if line]
    merged = reduce(deep_merge, as_json)
    if "detail" in merged:
        raise ValueError(merged["detail"])
    return merged
