import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.data.schemas import VerStack

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

def log(string: str, force: bool = False):
    if settings.DEBUG or force:
        logger.info(string)
        
class Settings(BaseSettings):

    LOCAL_CACHE_HOST: str = 'orc.local_cache'
    LOCAL_CACHE_PORT: int = 6379
    DB_HOST: str = 'orc.db'
    REQUESTER_HOST: str = 'orc.requester'

    LOCAL_CACHE_PASS: str
    DB_PASS: str
    REQUESTER_PASS: str

    REDIS_TTL: int = 900

    DEBUG = False

    model_config = SettingsConfigDict(
        env_file="src/.env",
        env_file_encoding="utf-8",
    )
    
settings = Settings() # type: ignore[call-arg]