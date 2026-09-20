import src.dependency_handling as dependency_handling

from src.external import _requester
from src.data.schemas import ProjectDantic, VerStack, ProjStack, VersionDantic, Loader, GameVersion
import src.pull_from as pull_from

async def main_pipeline(id_list: set[str]) -> ProjStack:
    projstack = await _requester.get_projects(id_list)
    verstack = await _versions_processing(projstack.valid)
    projstack = _build_tree(projstack, verstack)
    return projstack

async def _versions_processing(projects: dict[str, ProjectDantic], pull_from = pull_from) -> VerStack:

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

def _build_tree(projstack: ProjStack, verstack: VerStack) -> ProjStack:
    for project_obj in projstack.valid.values():
        for version_str in project_obj.versions:
            version_obj = verstack.valid[version_str]
            for loader in version_obj.loaders:
                for game_ver_str in version_obj.game_versions:
                    _handle_branch(project_obj, loader, game_ver_str, version_obj)
    return projstack

def _handle_branch(project: ProjectDantic, loader_str: str, game_ver_str: str, version: VersionDantic) -> None:

    try:
        loader_obj = project.tree[loader_str]
    except KeyError:
        loader_obj = Loader(name=loader_str)

    try:
        game_ver_obj = loader_obj.game_versions[game_ver_str]
    except KeyError:
        game_ver_obj = GameVersion(name=game_ver_str)

    game_ver_obj.versions[version.id] = version
    loader_obj.game_versions[game_ver_str] = game_ver_obj
    project.tree[loader_str] = loader_obj