import httpx

from src.c_exceptions import *
from src.util import settings
from src.data import validation
from src.data.schemas import VerStack, ProjStack

limiter = httpx.Limits(max_connections=10)
client = httpx.AsyncClient(limits=limiter)

async def get_projects(id_list: set[str]) -> ProjStack:
    host: str = settings.REQUESTER_HOST + '/projects'
    raw_response = await _send_request(id_list, host)
    projstack = validation.projects_from_api(raw_response)
    return projstack

async def get_versions(id_list: set[str]) -> VerStack:
    host: str = settings.REQUESTER_HOST + '/versions'
    raw_response = await _send_request(id_list, host)
    verstack = validation.versions_from_api(raw_response)
    return verstack

async def _send_request(id_list: set[str], endpoint: str) -> list[dict]:
    request = await client.get(endpoint, params={'ids': list(id_list)})
    request.raise_for_status()
    data = request.json()
    return data
