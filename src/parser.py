import asyncio, httpx, json

from typing import Any

from pydantic import ValidationError

import src.cfg as cfg
from src.schemas import ProjectDantic
from src.ver_repo import *
from src.utility import *

from more_itertools import chunked
from copy import deepcopy

class ModrinthProjectStack:
    
    def __init__(self) -> None:
        self.mods: list[ProjectDantic] = []
        self.shaders: list[ProjectDantic] = []
        self.resources: list[ProjectDantic] = []

        self.versions_tree: dict[str, dict[str, list[str]]] = {}

    def _mods_to_tree(self) -> None:
        
        for project in self.mods:
            for ver in project.parsed_versions:
                for loader in ver.loaders:
                    
                    if loader not in self.versions_tree.keys():
                        self.versions_tree[loader] = {}
                    
                    for game_ver in ver.game_versions:
                    
                        if game_ver not in self.versions_tree[loader]:
                            self.versions_tree[loader][game_ver] = []

                        self.versions_tree[loader][game_ver].append(ver.id)

    def _shaders_to_tree(self) -> None:

        for project in self.shaders:
            for ver in project.parsed_versions:
                
                for loader in self.versions_tree.keys():
                    for game_ver in ver.game_versions:

                        if game_ver not in self.versions_tree[loader]:
                            self.versions_tree[loader][game_ver] = []

                        self.versions_tree[loader][game_ver].append(ver.id)

    def _resources_to_tree(self) -> None:

        for project in self.resources:
            for ver in project.parsed_versions:
                
                for loader in self.versions_tree.keys():
                    for game_ver in ver.game_versions:

                        if game_ver not in self.versions_tree[loader]:
                            self.versions_tree[loader][game_ver] = []

                        self.versions_tree[loader][game_ver].append(ver.id)

    def make_ver_tree(self) -> dict[str, dict[str, list[str]]]:
        
        """
        Bulds and returns versions tree in the following format: loader -> game_version -> list[versions_id]
        """

        self._mods_to_tree()
        self._shaders_to_tree()
        self._resources_to_tree()

        return self.versions_tree

class Modrinth:

    timeout = httpx.Timeout(5.0, connect=5.0)
    project_api_url = 'https://api.modrinth.com/v2/projects'

    @classmethod
    async def _single_segment_request(cls, client: httpx.AsyncClient, slug_list: list[str]) -> list[dict]:

        json_string = json.dumps(slug_list)

        response = await client.get(
            cls.project_api_url,
            params={"ids": json_string}
        )

        try:
            response.raise_for_status()
        except Exception as ex:
            log(str(ex), True)

        return response.json()
        
    @classmethod
    async def _request_projects(cls, projects: str) -> list[list[dict]]:

        """
        Requests projects info with async batch requests

        :param projects: A string containing Modrinth project URLs, separated into lines.
        :type projects: str
        :return: Segmented list with requsts results
        :rtype: list[list[dict]]
        """

        slug_list = [url.rsplit('/', 1)[1] for url in projects.split('\n')]

        log(f'Parsing {len(slug_list)} projects')
        
        projects_slugs_segmented = list(chunked(slug_list, cfg.COLLECTION_SEGMENT_SIZE))

        async with httpx.AsyncClient(timeout=cls.timeout) as client:
            results = await asyncio.gather(
                *(cls._single_segment_request(client, segment) for segment in projects_slugs_segmented)
            )

        return results
    
    @classmethod
    def _validate_projects(cls, projects: list[list[dict]]) -> tuple[list[ProjectDantic], list[dict]]:

        """
        Validates requested data with pydantic model
        
        :param projects: List with segmented requsts results
        :type projects: list[list[dict]]
        :return: Validated projects pydantic models and raw data list of projects that failed to validate 
        :rtype: tuple[list[ProjectDantic], list[dict[Any, Any]]]
        """
        
        parsed = []
        failed = []

        for segment in projects:
            for project in segment:
                try:
                    parsed.append(ProjectDantic.model_validate(project))
                except ValidationError:
                    failed.append(InvalidProjectDantic.model_validate(project))

        return parsed, failed

    @classmethod
    async def _enrich_projects_with_versions(cls, projects: list[ProjectDantic]) -> None:

        """
        Mutates projects models by adding parsed and invalid versions
        
        :param projects: Projects list
        :type projects: list[ProjectDantic]
        """
        
        for proj in projects:
            proj.parsed_versions, proj.invalid_versions = await VerRepo.get([ver for ver in proj.versions])

    @classmethod
    def _enrich_stack_with_projects(cls, stack: ModrinthProjectStack, projects: list[ProjectDantic]):

        """
        Mutates projects models by sorting projects to stack by project type
        
        :param stack: Projects stack object
        :type stack: ProjectStack
        :param projects: Parsed projects list
        :type projects: list[ProjectDantic]
        """

        for project in projects:
            log(f'')
            log(f'Project: {project.title}')
            if project.project_type == 'mod':
                stack.mods.append(project)
            if project.project_type == 'resourcepack':
                stack.resources.append(project)
            if project.project_type == 'shader':
                stack.shaders.append(project)

    @classmethod
    def final_check(cls, user_projects_count: int, parsed_projects_json: dict[str, dict[str, list[str]]], acceptable_fail_count: int = 0) -> dict[str, dict[str, list[str]]]:
        
        """
        Iterate through every loader and game version combination in parsed projects and check if it has enough parsed versions.
        If loader and game_version has equal or higher parsed versions then projects offered by user, than combination is considered valid.
        In other case combination deletes. If loader has zero game versions, it deletes
        
        :param user_projects_count: Count of projects that offered by user and successfully validated
        :type user_projects_count: int
        :param parsed_projects_json: Versions tree
        :type parsed_projects_json: dict[str, dict[str, list[str]]]
        :return: Versions tree after count check
        :rtype: dict[str, dict[str, list[str]]]
        """

        for loader in deepcopy(parsed_projects_json):
            for game_ver in deepcopy(parsed_projects_json[loader]):
                
                if len(parsed_projects_json[loader][game_ver]) < user_projects_count - acceptable_fail_count:
                    del parsed_projects_json[loader][game_ver]

            if len(parsed_projects_json[loader].keys()) <= 0:
                del parsed_projects_json[loader]

        return parsed_projects_json

    @classmethod
    async def parse_projects(cls, projects_urls: str) -> dict[str, dict[str, list[str]]]:
        
        """
        Parsing given projects info, parsing projects versions, building projects stack and returning json string winth available modloaders and game versions
        
        :param projects: Modrinth projects urls divided by rows
        :type projects: str
        :return: Versions tree in JSON string
        :rtype: dict
        """
        
        results = await cls._request_projects(projects_urls)
        valid_projs, failed_projs = cls._validate_projects(results)

        await cls._enrich_projects_with_versions(valid_projs)
        
        projects_stack = ModrinthProjectStack()
        cls._enrich_stack_with_projects(projects_stack, valid_projs)

        json_result = projects_stack.make_ver_tree()

        final_list = cls.final_check(len(valid_projs), json_result)

        return final_list
            
    