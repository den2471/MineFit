import src.dependency_handling as dependency_handling

from external import _requester
from src.data.schemas import ProjectDantic, VerStack, ProjectTree, ProjStack
import pull_from as pull_from

async def main_pipeline(id_list: set[str]) -> ProjectTree:
    tree = ProjectTree()
    projstack = await _projetcs_processing(set(id_list))
    tree = _tree_building(projstack)
    return tree

async def _projetcs_processing(id_list: set[str]) -> ProjStack:
    projstack = await _requester.get_projects(id_list)
    verstack = await _versions_processing(projstack.valid)
    projstack = _enrich_projects_with_versions(projstack, verstack)
    return projstack

async def _versions_processing(projects: dict[str, ProjectDantic]) -> VerStack:

    id_list: set[str] = set()

    verstack = VerStack()

    for proj in projects.values():
        id_list.update(proj.versions)

    verstack, remain = await pull_from.local_cache(id_list, verstack)

    if remain:
        verstack, remain = await pull_from.db(remain, verstack)           

    if remain:
        verstack = await pull_from.api(remain, verstack)

    verstack = await dependency_handling.main_pipeline(verstack)

    return verstack

def _enrich_projects_with_versions(projstack: ProjStack, verstack: VerStack) -> ProjStack:
    for project in projstack.valid.values():
        for ver in project.versions:
            try:
                project.parsed_versions[ver] = verstack.valid[ver]
            except KeyError:
                project.invalid_versions.add(ver)
    return projstack

def _tree_building(projstack: ProjStack) -> ProjectTree:
    ...