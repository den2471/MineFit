from redis.asyncio import Redis
from pydantic import ValidationError

from src.util import settings
from src.data.schemas import VersionDantic

redis = Redis(
    host=settings.LOCAL_CACHE_HOST,
    port=settings.LOCAL_CACHE_PORT,
    password=settings.LOCAL_CACHE_PASS,
    decode_responses=True
)

async def get_versions(id_list: set[str]) -> dict[str, VersionDantic]:
    pipe = redis.pipeline()
    for id in id_list:
        pipe.getex(id, ex=settings.REDIS_TTL)
    raw_data = await pipe.execute()
    result = {}
    for obj in raw_data:
        if isinstance(obj, dict):
            try:
                result[obj.get('id', 'null')] = VersionDantic.model_validate(obj)
            except ValidationError:
                pass
    return result

async def add_versions(versions: list[VersionDantic]):
    pipe = redis.pipeline()
    for ver in versions:
        pipe.set(ver.id, ver.model_dump_json(), ex=settings.REDIS_TTL)
    await pipe.execute()