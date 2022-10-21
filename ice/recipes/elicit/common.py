import json
import os

from functools import reduce
from pathlib import Path

import httpx

from dotenv import dotenv_values
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_random_exponential

from ice.cache import diskcache


script_dir = Path(__file__).parent
root_dir = script_dir.parent.parent.parent
config = dotenv_values(root_dir / ".env")

ELICIT_AUTH_TOKEN = os.getenv("ELICIT_AUTH_TOKEN", config.get("ELICIT_AUTH_TOKEN"))

if not ELICIT_AUTH_TOKEN:
    raise Exception(
        "ELICIT_AUTH_TOKEN not found. Please look it up by checking idToken in cookies for elicit.org and add it to .env."
    )


def _merge(recurse, path: list, base: dict, nxt: dict) -> dict:
    for k, v in nxt.items():
        if k not in base:
            base[k] = v
        else:
            base[k] = recurse(recurse, path + [k], base[k], v)
    return base


def deep_merge(base, nxt):
    """
    Performs a *limited* deep merge of nxt into base.
    Type differences are overriden by nxt.
    Lists are extended, but elements are not changed or recursed into.
    Sets are unioned but not recursed into.
    """

    def merge_strategy(
        merge_strategy,
        path: list,
        base,
        nxt,
    ):
        if not (isinstance(base, type(nxt)) or isinstance(nxt, type(base))):
            return nxt
        elif isinstance(nxt, dict):
            return _merge(merge_strategy, path, base, nxt)
        elif isinstance(nxt, list) or isinstance(nxt, tuple):
            return base + nxt
        elif isinstance(nxt, set):
            return base | nxt
        return nxt

    return merge_strategy(merge_strategy, [], base, nxt)


@diskcache()
@retry(stop=stop_after_attempt(2), wait=wait_random_exponential(2))
def send_elicit_request(*, request_body, endpoint: str):
    assert ELICIT_AUTH_TOKEN is not None, "ELICIT_AUTH_TOKEN is not set"
    headers = {
        "Content-Type": "application/json",
        "Authorization": ELICIT_AUTH_TOKEN,
    }
    chunks = []
    with httpx.stream(
        "POST",
        endpoint,
        json=request_body,
        headers=headers,
        timeout=40,
    ) as r:
        for chunk in r.iter_text():
            print(chunk)
            chunks.append(chunk)
    joined = "".join(chunks)
    split_on_newlines = joined.split("\n")
    as_json = [json.loads(line) for line in split_on_newlines if line]
    merged = reduce(deep_merge, as_json)
    if "detail" in merged:
        raise ValueError(merged["detail"])
    return merged
