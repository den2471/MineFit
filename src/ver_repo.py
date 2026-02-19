import asyncio
import httpx
import json

import src.cfg as cfg
from copy import deepcopy
from src.utility import *
from src.db import VerStack, Session
import src.db as db
from src.c_exceptions import *
from src.schemas import *

from sqlalchemy.ext.asyncio import AsyncSession
from more_itertools import chunked
from pydantic import ValidationError

class VerRepo:

    _timeout = httpx.Timeout(10.0)
    _semaphore = asyncio.Semaphore(20)

    _versions_api_url = 'https://api.modrinth.com/v2/versions'

    @classmethod
    async def _segment_request(cls, client: httpx.AsyncClient, version_list_segment: list[str]) -> list[dict]:

        """
        Request and returns versions data segment from Modrinth
        
        :param client: Client
        :type client: httpx.AsyncClient
        :param version_list_segment: List of versions ids
        :type version_list_segment: list[str]
        :return: Versions data if json
        :rtype: list[dict[Any, Any]]
        """

        
        ids_param = json.dumps(version_list_segment)

        response = await client.get(
            cls._versions_api_url, 
            params={'ids': ids_param}
        )
        
        try:
            response.raise_for_status()
        except Exception as ex:
            logger.error(f'{ex}')

        response = response.json()

        return response

    @classmethod
    async def _ver_stack_check(cls, ver_id_list: list[str], ver_stack: VerStack) -> list[str] | None:
        
        """
        Check versions from received list is already parsed and pushed into stack.
        This method is for preventing infinite loop in case of mutual dependencies.
        
        :param ver_id_list: List of versions ids
        :type ver_id_list: list[str]
        :param ver_stack: Global stack of versions
        :type ver_stack: VerStack
        """

        for ver_id in deepcopy(ver_id_list):
            if ver_id in list(ver_stack.parsed.keys()) or ver_id in list(ver_stack.invalid.keys()):
                ver_id_list.remove(ver_id)
            
        return ver_id_list

    @classmethod
    async def _ver_stack_enrich(cls, results: list[list[dict]], ver_stack: VerStack):
        
        """
        Validates segmented list of json responces from api and puts versions in global stack
        
        :param results: Versions segmented
        :type results: list[list[dict]]
        :param ver_stack: Global stack of versions
        :type ver_stack: VerStack
        :return: Description
        :rtype: VerStack
        """

        for segment in results:
            for ver in segment:
                try:
                    model = VersionDantic.model_validate(ver)
                    ver_stack.parsed[model.id] = model
                except ValidationError as ex:
                    model = InvalidVersionDantic.model_validate({'id': ver.get('id', 'null')})
                    ver_stack.invalid[model.id] = model
    
    @classmethod
    async def _versions_request(cls, ver_id_list: list[str]) -> list[list[dict]]:

        """
        Make async batch requests to api
        
        :param ver_id_list_segmented: List if version ids
        :type ver_id_list_segmented: list[list[str]]
        :return: Segmented list of api responses
        :rtype: list[list[dict]]
        """
        
        ver_id_list_segmented = list(chunked(ver_id_list, cfg.COLLECTION_SEGMENT_SIZE))

        limits = httpx.Limits(
            max_connections=cfg.MAX_CONCURRENT_REQUESTS,
            max_keepalive_connections=cfg.KEEP_ALIVE_CONNECTION,
        )
        
        async with httpx.AsyncClient(timeout=cls._timeout, limits=limits) as client:
            results = await asyncio.gather(
                *(cls._segment_request(client, segment) for segment in ver_id_list_segmented)
            )

        return results
    
    @classmethod
    async def _dep_ids_aggregate(cls, ver_stack: VerStack) -> list[str]:

        """
        Mutates gloabal versions stack.
        If dependency has wrong data, parent versions moves from parsed to invalid. 
        
        :param ver_stack: Global versions stack
        :type ver_stack: VerStack
        :return: List of dependencies versions ids
        :rtype: list[str]
        """

        dep_id_list: list[str] = []
        ver_dantic_list = list(ver_stack.parsed.values())

        for ver in ver_dantic_list:
            dep_id_list.extend(ver.dependencies)

        return dep_id_list
    
    @classmethod
    async def _filter_invalid_vers_by_deps(cls, ver_stack: VerStack) -> None:
        
        """
        Iterates through successfully validated versions and check if it has atleast one dependency that failed to validate.
        if version has invalid dependency, then version moves from successfully validated list to invalid list.
        
        :param ver_stack: Global stack of processed versions
        :type ver_stack: VerStack
        """

        parsed = deepcopy(ver_stack.parsed)
        invalid = deepcopy(ver_stack.invalid)

        for ver in parsed.values():
            for dep in ver.dependencies:
                if dep in list(invalid.keys()) or dep is None:
                    del ver_stack.parsed[ver.id]
                    ver_stack.invalid[ver.id] = InvalidVersionDantic.model_validate({'id': ver.id})
                    break

    @classmethod
    async def add(cls, session: AsyncSession, ver_id_list: list[str], ver_stack: VerStack) -> VerStack:

        """
        Pipeline to request, validate and add project version to repo.
        Check global versions stack -> request to api -> validate to pydantic models -> add models to stack -> check dependencies -> repeat from start -> return global versions stack
        
        :param ver_id_list: Description
        :type ver_id_list: list[str]
        :param ver_in_work: Description
        :type ver_in_work: set[str] | None
        :return: Description
        :rtype: tuple[list[VersionDantic], dict[str, InvalidVersionDantic]]
        """

        
        ver_id_list_filtered = await cls._ver_stack_check(ver_id_list, ver_stack)
        
        if not ver_id_list_filtered:
            return ver_stack
        
        log(f'Fetching {len(ver_id_list_filtered)} versions')

        request_response = await cls._versions_request(ver_id_list)

        await cls._ver_stack_enrich(request_response, ver_stack)
        
        dep_id_list = list(set(await cls._dep_ids_aggregate(ver_stack)))

        log(f'{len(dep_id_list)} dependencies')

        await cls.add(session, dep_id_list, ver_stack)
        
        await cls._filter_invalid_vers_by_deps(ver_stack)

        return ver_stack
        
    @classmethod
    async def get(cls, ver_id_list: set[str]) -> VerStack:

        log(f'{len(ver_id_list)} versions')

        ver_id_segmented = list(chunked(ver_id_list, cfg.COLLECTION_SEGMENT_SIZE))

        ver_stack = VerStack()

        await asyncio.gather(
            *(db.enrich_ver_stack(segment, ver_stack) for segment in ver_id_segmented)
        )
        
        log(f'Got {len(ver_stack.parsed)} saved')
        log(f'Got {len(ver_stack.invalid)} invalid')

        for ver in list(ver_stack.parsed.values()):
            ver_id_list.remove(ver.id)

        for ver in list(ver_stack.invalid.values()):
            ver_id_list.remove(ver.id)

        remain = list(ver_id_list)

        log(f'{len(remain)} missing in db')

        if remain:
            async with Session() as session:
                await cls.add(session, remain, ver_stack)
                session_data = list(ver_stack.parsed.values()) + list(ver_stack.invalid.values())
                log(f'Cached {len(ver_stack.parsed)} parsed versions and {len(ver_stack.invalid)} invalid versions')
                await db.add_versions_to_session(session, session_data)
                await db.commit_changes(session)

        return ver_stack