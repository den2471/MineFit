import asyncio
import httpx
import json

import src.cfg as cfg
from copy import deepcopy
from src.utility import *
from src.db import Session, get_versions, save_versions, commit_changes
from src.c_exceptions import *
from src.schemas import *

from more_itertools import chunked
from pydantic import ValidationError

class VerRepo:

    _timeout = httpx.Timeout(10.0)
    _semaphore = asyncio.Semaphore(20)

    _versions_api_url = 'https://api.modrinth.com/v2/versions'

    @classmethod
    async def _segment_request(cls, client: httpx.AsyncClient, version_list_segment: list[str]) -> list[dict]:

        """
        Request data for versions segment from Modrinth
        
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
    def _versions_validate(cls, version: dict) -> VersionORM | InvalidVersionORM:

        try:
            model = VersionDantic.model_validate(version)
            return VersionORM(**model.model_dump())
        except ValidationError:
            model = InvalidVersionDantic.model_validate(version)
            return InvalidVersionORM(**model.model_dump())
        
    @classmethod
    async def _check_dependencies(cls, version: VersionORM) -> tuple[list[VersionORM], list[InvalidVersionORM]]:
        
        parsed: list[VersionORM] = []
        invalid: list[InvalidVersionORM] = []

        for version in deepcopy(parsed):
            _parsed, _invalid = await cls.get(version.dependencies)
            if _invalid:
                parsed.remove(version)
                invalid.append(InvalidVersionORM(id=version.id))

        return parsed, invalid

    @classmethod
    async def add(cls, version_id_list: list[str], working_with: set[str] | None = None) -> tuple[list[VersionORM], list[InvalidVersionORM]]:

        log(f'Fetching {len(version_id_list)} versions')
        
        if working_with:
            version_id_list = list(set(version_id_list) - set(working_with))
        else:
            working_with = set([ver for ver in version_id_list])
            
        segmented_list = chunked(version_id_list, cfg.COLLECTION_SEGMENT_SIZE)

        async with httpx.AsyncClient(timeout=cls._timeout) as client:
            results = await asyncio.gather(
                *(cls._segment_request(client, segment) for segment in segmented_list)
            )

        parsed: list[VersionORM] = []
        invalid: list[InvalidVersionORM] = []

        for segment in results:
            for ver in segment:
                result = cls._versions_validate(ver)
                if isinstance(result, VersionORM):
                    parsed.append(result)
                else:
                    invalid.append(result)
        
        for ver in parsed:
            await cls._check_dependencies(ver)

        await save_versions(parsed+invalid)

        log(f'Cached {len(parsed)} parsed versions')
        log(f'Cached {len(invalid)} invalid versions')

        return parsed, invalid
        
    @classmethod
    async def get(cls, version_list: list[str]) -> tuple[list[VersionORM], list[InvalidVersionORM]]:

        log(f'- Getting {len(version_list)} versions')

        ver_id_segmented = list(chunked(version_list, cfg.COLLECTION_SEGMENT_SIZE))

        results = await asyncio.gather(
            *(get_versions(segment) for segment in ver_id_segmented)
        )

        parsed_from_db: list[VersionORM] = []
        invalid_from_db: list[InvalidVersionORM] = []

        for segment in results:
            parsed_from_db.extend(segment[0])
            invalid_from_db.extend(segment[1])
        
        log(f'- Got {len(parsed_from_db)} saved')
        log(f'- Got {len(invalid_from_db)} invalid')

        for ver in parsed_from_db:
            version_list.remove(ver.id)

        for ver in invalid_from_db:
            version_list.remove(ver.id)

        remain = [id for id in version_list]

        log(f'- {len(remain)} missing in db')

        if remain:
            _parsed, _invalid = await cls.add(remain)
            parsed_from_db.extend(_parsed)
            invalid_from_db.extend(_invalid)

        await commit_changes()

        return parsed_from_db, invalid_from_db