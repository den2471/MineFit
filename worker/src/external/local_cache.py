from redis.asyncio import Redis
from typing import Any

from src.util import settings
from src.data.schemas import VersionDantic, VerStack
from src.data import validation

redis = Redis(
    host=settings.LOCAL_CACHE_HOST,
    port=settings.LOCAL_CACHE_PORT,
    password=settings.LOCAL_CACHE_PASS,
    decode_responses=True
)

async def get_versions(id_list: set[str]) -> VerStack:
    pipe = redis.pipeline()
    for id in id_list:
        pipe.getex(id, ex=settings.REDIS_TTL)
    raw_data = await pipe.execute()
    verstack = validation.versions_from_cache(raw_data)
    return verstack

async def add_versions(versions: list[VersionDantic]):
    pipe = redis.pipeline()
    for ver in versions:
        pipe.set(ver.id, ver.model_dump_json(), ex=settings.REDIS_TTL)
    await pipe.execute()