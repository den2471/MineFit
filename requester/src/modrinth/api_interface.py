import httpx, random, json
from httpx import Response
from asyncio import gather, sleep
from os import getenv

def get_required_env(name: str) -> str:
    value = getenv(name)
    if value is None:
        raise ValueError(f'No {name} presented. Check if environment has the right variables.')
    return value

from src.util import settings

projects_endpoint = settings.PROJECTS_ENDPOINT
versions_endpoint = settings.VERSIONS_ENDPOINT

async def request_projects(id_list: list[list[str]], client: httpx.AsyncClient) -> list[dict]:
    return await _batch_request(id_list, projects_endpoint, client)

async def request_versions(id_list: list[list[str]], client: httpx.AsyncClient) -> list[dict]:
    return await _batch_request(id_list, versions_endpoint, client)

async def _batch_request(id_list: list[list[str]], endpoint: str, client: httpx.AsyncClient) -> list[dict]:
    segmented_result = await gather(
        *(_single_request(client, endpoint, segment) for segment in id_list)
    )
    result = []
    for segment in segmented_result:
        result.extend(segment)
    return result

async def _single_request(client: httpx.AsyncClient, endpoint: str, ids: list[str] | None = None) -> list[dict]:
    await sleep(random.random() * 2) # jitter
    responce = await client.get(endpoint, params={'ids': json.dumps(ids)})
    responce.raise_for_status()
    return responce.json()