import json

from os import environ
from pathlib import Path
from typing import Any
from typing import Optional
from typing import TYPE_CHECKING

from pydantic import BaseSettings

if TYPE_CHECKING:
    AnyHttpUrl = str
else:
    from pydantic import AnyHttpUrl

from .logging import log_lock

OUGHT_ICE_DIR = Path(environ.get("OUGHT_ICE_DIR", Path.home() / ".ought-ice"))

_env_path = OUGHT_ICE_DIR / ".env"


class Settings(BaseSettings):
    OPENAI_ORG_ID: str = ""
    OUGHT_INFERENCE_URL: AnyHttpUrl = "https://prod.elicit.org"
    GOLD_STANDARDS_CSV_PATH: Path = (
        Path(__file__).parent.parent / "gold_standards/gold_standards.csv"
    )
    GS_QUOTE_FOUND_THRESHOLD: float = 0.75
    OUGHT_ICE_HOST: str = "0.0.0.0"
    OUGHT_ICE_PORT: int = 8935
    OUGHT_ICE_AUTO_SERVER: bool = True
    OUGHT_ICE_AUTO_BROWSER: bool = True
    PAPER_DIR: Path = Path(__file__).parent.parent / "papers"

    # note these attributes are read differently- see [__getattribute__]
    OPENAI_API_KEY: str = ""
    OUGHT_INFERENCE_API_KEY: str = ""
    ELICIT_AUTH_TOKEN: str = ""

    def __get_and_store(self, setting_name: str, prompt: Optional[str] = None) -> str:
        # We use [__getattribute__] to read these attributes, so that we can
        # prompt the user for them if they are not already set.
        if prompt is None:
            prompt = f"Enter {setting_name}: "
        if self.__dict__[setting_name] == "":
            with log_lock:
                value = input(prompt)
            setattr(self, setting_name, value)
            with open(_env_path, "a") as f:
                # [json.dumps] to escape quotes
                f.write(f"{setting_name}={json.dumps(value)}\n")
        return self.__dict__[setting_name]

    def __getattribute__(self, name: str) -> Any:
        match name:
            case "OPENAI_API_KEY":
                return self.__get_and_store(
                    "OPENAI_API_KEY",
                    prompt="Enter OpenAI API key (you can get this from https://beta.openai.com/account/api-keys): ",
                )
            case "OUGHT_INFERENCE_API_KEY":
                return self.__get_and_store("OUGHT_INFERENCE_API_KEY")
            case "ELICIT_AUTH_TOKEN":
                return self.__get_and_store(
                    "ELICIT_AUTH_TOKEN",
                    prompt="Enter Elicit Auth Token (you can find it by checking idToken in cookies for Elicit. The cookie should NOT start with Bearer; it should just be a string of letters and numbers): ",
                )
            case _:
                return super().__getattribute__(name)


# Note that fields are loaded from pydantic in a particular priority ordering. See
# https://docs.pydantic.dev/usage/settings/#field-value-priority
settings = Settings(
    _env_file=_env_path if _env_path.exists() else None, _env_file_encoding="utf-8"
)

CACHE_DIR = OUGHT_ICE_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def server_url() -> str:
    return f"http://{settings.OUGHT_ICE_HOST}:{settings.OUGHT_ICE_PORT}"
