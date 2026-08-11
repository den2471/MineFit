import httpx

from src.c_exceptions import *
from src.util import settings

limiter = httpx.Limits(max_connections=10)
client = httpx.AsyncClient(limits=limiter)

async def get_projects(id_list: set[str]) -> dict:
    host: str = settings.REQUESTER_HOST + '/projects'
    return await _send_request(id_list, host)

async def get_version(id_list: set[str]) -> dict:
    host: str = settings.REQUESTER_HOST + '/versions'
    return await _send_request(id_list, host)

async def _send_request(id_list: set[str], endpoint: str) -> dict:
    request = await client.get(endpoint, params={'ids': list(id_list)})
    request.raise_for_status()
    data = request.json()
    return data
