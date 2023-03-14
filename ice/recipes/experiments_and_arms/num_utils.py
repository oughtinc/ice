import re
from collections.abc import Sequence

from numerizer import numerize
from structlog.stdlib import get_logger

log = get_logger()


def _extract_nums(text: str) -> Sequence[str]:
    numerized = numerize(text)
    # TODO: handle commas, decimals
    return re.findall("[0-9]+", numerized)


def extract_nums(text: str) -> list[int]:
    return [int(num) for num in _extract_nums(text)]


def strip_enumeration_prefix(text: str) -> str:
    return re.sub(r"^\w*\s*\d+(\.|\))", "", text.strip()).strip()
