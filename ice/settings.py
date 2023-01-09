from os import environ
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseSettings

if TYPE_CHECKING:
    AnyHttpUrl = str

else:
    from pydantic import AnyHttpUrl


OUGHT_ICE_DIR = Path(environ.get("OUGHT_ICE_DIR", Path.home() / ".ought-ice"))

_env_path = OUGHT_ICE_DIR / ".env"


class Settings(BaseSettings):
    # TODO there's gotta be a cleaner way to do this-
    # maybe a way to have a base class that has all the
    # settings, and then a subclass that has the
    # settings that are prompted for?
    OPENAI_API_KEY: str = ""  # TODO prompt this
    OPENAI_ORG_ID: str = ""
    OUGHT_INFERENCE_API_KEY: str = ""  # TODO prompt and save this
    OUGHT_INFERENCE_URL: AnyHttpUrl = "https://prod.elicit.org"
    ELICIT_AUTH_TOKEN: str = ""  # TODO prompt and save this
    GOLD_STANDARDS_CSV_PATH: Path = (
        Path(__file__).parent.parent / "gold_standards/gold_standards.csv"
    )
    GS_QUOTE_FOUND_THRESHOLD: float = 0.75
    OUGHT_ICE_HOST: str = "0.0.0.0"
    OUGHT_ICE_PORT: int = 8935
    OUGHT_ICE_AUTO_SERVER: bool = True
    OUGHT_ICE_AUTO_BROWSER: bool = True
    PAPER_DIR: Path = Path(__file__).parent.parent / "papers"

    def get_setting_with_prompting(self, setting_name: str) -> str:
        # TODO there has to be a cleaner way to do this hmmmm
        # TODO add prompting
        # TODO squash these commits
        if getattr(self, setting_name) == "":
            value = input(f"Enter {setting_name}: ")
            # TODO are get/setattr really what they appear to be
            setattr(self, setting_name, value)
            # TODO test this
            with open(_env_path, "a") as f:
                f.write(f"{setting_name}={value}")
        return getattr(self, setting_name)


settings = Settings(
    _env_file=_env_path if _env_path.exists() else None, _env_file_encoding="utf-8"
)

CACHE_DIR = OUGHT_ICE_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def server_url() -> str:
    return f"http://{settings.OUGHT_ICE_HOST}:{settings.OUGHT_ICE_PORT}"
