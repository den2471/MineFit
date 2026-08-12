from pydantic import ValidationError

from src.external import local_cache, db, requester
from src.data.schemas import ProjectDantic, InvalidVersionORM, VerStack, ProjectTree, ProjStack, VersionDantic

async def main_pipeline(id_list: set[str]) -> ProjectTree:
    tree = ProjectTree()
    projstack = await _projetcs_processing(set(id_list))
    return tree

async def _projetcs_processing(id_list: set[str]) -> ProjStack:
    projstack = await requester.get_projects(id_list)
    verstack = await _versions_processing(projstack.valid)
    projstack = _enrich_projects_with_versions(projstack, verstack)
    return projstack

async def _versions_processing(projects: dict[str, ProjectDantic]) -> VerStack:

    id_list: set[str] = set()

    verstack = VerStack()

    for proj in projects.values():
        id_list.update(proj.versions)

    verstack, remain = await _from_local_cache(id_list, verstack)

    if remain:
        verstack, remain = await _from_db(remain, verstack)           

    if remain:
        verstack = await _from_api(remain, verstack)

    verstack = await _dependency_handling(verstack)

    return verstack

async def _from_local_cache(id_list: set[str], main_verstack: VerStack) -> tuple[VerStack, set[str]]:
    cached_verstack = await local_cache.get_versions(id_list)
    remain = _clean_id_list(id_list, cached_verstack)
    main_verstack.merge(cached_verstack)
    return main_verstack, remain

async def _from_db(id_list: set[str], main_verstack: VerStack) -> tuple[VerStack, set[str]]:
    stored_verstack = await db.get_versions(id_list)
    remain = _clean_id_list(id_list, stored_verstack)
    main_verstack.merge(stored_verstack)
    return main_verstack, remain

async def _from_api(id_list: set[str], main_verstack: VerStack) -> VerStack:
    requested_verstack = await requester.get_versions(id_list)
    remain = _clean_id_list(id_list, requested_verstack)
    if remain:
        requested_verstack.invalid.update(remain)
    main_verstack.merge(requested_verstack)
    if requested_verstack.invalid:
        await db.push_versions([InvalidVersionORM(id=id) for id in requested_verstack.invalid])
    return main_verstack

async def _dependency_handling(verstack: VerStack) -> VerStack:

    dep_list = _update_dep_list(set(), verstack)

    while dep_list:

        dep_list = _update_dep_list(dep_list, verstack)
        dep_list = _clean_id_list(dep_list, verstack)

        if dep_list:

            verstack, remain = await _from_local_cache(dep_list, verstack)
            
            if remain:
                verstack, remain = await _from_db(remain, verstack)           
        
            if remain:
                verstack = await _from_api(remain, verstack)

    verstack = _enrich_versions_with_deps(verstack)
    return verstack

def _enrich_versions_with_deps(verstack: VerStack) -> VerStack:
    failed = True
    skip: set[str] = set()
    while failed:
        failed = False
        to_process: dict[str, VersionDantic] = {}

        for ver in verstack.valid.values():
            if ver.id not in skip:
                to_process[ver.id] = ver

        for ver in to_process.values():
            for dep in ver.dependencies:
                try:
                    verstack.valid[ver.id].parsed_deps[dep] = verstack.valid[dep]
                except KeyError:
                    failed = True
                    verstack.valid.pop(ver.id, None)
                    verstack.invalid.add(ver.id)
                    break
    return verstack

def _parsing_completion_check(version: VersionDantic, skip: set[str] = set()) -> bool:
    ...

def _clean_id_list(id_list: set[str], verstack: VerStack):
    resolved = verstack.valid.keys() | verstack.invalid
    return id_list - resolved

def _update_dep_list(dep_list: set[str], verstack: VerStack) -> set[str]:
    for ver in verstack.valid.values():
        dep_list.update(ver.dependencies)
    return dep_list

def _enrich_projects_with_versions(projstack: ProjStack, verstack: VerStack) -> ProjStack:
    for project in projstack.valid.values():
        for ver in project.versions:
            try:
                project.parsed_versions[ver] = verstack.valid[ver]
            except KeyError:
                project.invalid_versions.add(ver)
    return projstack

def _tree_building(projects: dict[str, ProjectDantic]):
    ...