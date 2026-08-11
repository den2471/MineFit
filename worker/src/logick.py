from pydantic import ValidationError

from src.external import local_cache, requester
from src.data.schemas import ProjectDantic, VersionDantic, InvalidVersionDantic

async def main_pipeline(id_list: list[str]):

    validated, invalid = await _porjetcs_processing(set(id_list))

async def _porjetcs_processing(id_list: set[str]) -> tuple[tuple[ProjectDantic, ...], tuple[dict, ...]]:

    requested = await requester.get_projects(id_list)
    validated: list[ProjectDantic] = []
    invalid: list[dict] = []
    for row in requested:
        try:
            validated.append(ProjectDantic.model_validate(row))
        except ValidationError:
            invalid.append(row)
    return tuple(validated), tuple(invalid)

async def _versions_processing(projects: tuple[ProjectDantic]) -> tuple[ProjectDantic, ...]:

    id_list: set[str] = set()

    for proj in projects:
        id_list.update(proj.versions)

    cached = await local_cache.get_versions(id_list)
    for id in list(cached.keys()):
        id_list.remove(id)

    if id_list:
        requested = await requester.get_version(id_list)
        validated: list[VersionDantic] = []
        invalid: list[dict] = []
        for row in requested:
            try:
                validated.append(VersionDantic.model_validate(row))
            except:
                invalid.append(row)


    return 

async def _dependency_handling():
    ...

def tree_building(pprojects: tuple[ProjectDantic]):
    ... 