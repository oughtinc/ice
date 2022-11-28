from os import environ
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseSettings

if TYPE_CHECKING:
    AnyHttpUrl = str

else:
    from pydantic import AnyHttpUrl


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    OPENAI_ORG_ID: str = ""
    OUGHT_INFERENCE_API_KEY: str = ""
    OUGHT_INFERENCE_URL: AnyHttpUrl = "https://inference.elicit.org"
    GOLD_STANDARDS_CSV_PATH: str = "gold_standards/gold_standards.csv"
    GS_QUOTE_FOUND_THRESHOLD: float = 0.75


OUGHT_ICE_DIR = Path(environ.get("OUGHT_ICE_DIR", Path.home() / ".ought-ice"))

_env_path = OUGHT_ICE_DIR / ".env"
settings = Settings(
    _env_file=_env_path if _env_path.exists() else None, _env_file_encoding="utf-8"
)

CACHE_DIR = OUGHT_ICE_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
