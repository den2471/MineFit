from pydantic_settings import BaseSettings, SettingsConfigDict
from more_itertools import chunked
from typing import Any

def segment(obj: set[str], segment_size: int = 10) -> list[list[str]]:
    return list(chunked(obj, segment_size))

def validate_id_list(obj: Any) -> None | Any:
    if not isinstance(obj, list):
        return 'Whole list'
    else:
        for i in obj:
            if not isinstance(i, str):
                return i

class Settings(BaseSettings):

    PROJECTS_ENDPOINT: str = 'https://api.modrinth.com/v2/projects'
    VERSIONS_ENDPOINT: str = 'https://api.modrinth.com/v2/versions'

    model_config = SettingsConfigDict(
        env_file="src/.env",
        env_file_encoding="utf-8",
    )

settings = Settings() # type: ignore[call-arg]