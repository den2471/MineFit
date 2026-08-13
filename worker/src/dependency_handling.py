import pull_from as pull_from
from src.data.schemas import VerStack, VersionDantic
from src.util import _clean_id_list

async def main_pipeline(verstack: VerStack) -> VerStack:

    actual_versions_ids: set[str] = set(verstack.valid.keys())
    dep_list = _update_dep_list(set(), verstack)

    while dep_list:

        dep_list = _update_dep_list(dep_list, verstack)
        dep_list = _clean_id_list(dep_list, verstack)

        if dep_list:

            verstack, remain = await pull_from.local_cache(dep_list, verstack)
            
            if remain:
                verstack, remain = await pull_from.db(remain, verstack)           
        
            if remain:
                verstack = await pull_from.api(remain, verstack)

    verstack = _enrich_versions_with_deps(verstack, actual_versions_ids)
    return verstack

def _enrich_versions_with_deps(verstack: VerStack, actual_versions_ids: set[str]) -> VerStack:

    to_inspect: dict[str, VersionDantic] = {}
    for ver_id in actual_versions_ids:
        to_inspect[ver_id] = verstack.valid[ver_id]

    for version in to_inspect.values():
        if not _deep_inspection(version, verstack):
            verstack.valid.pop(version.id, None)
            verstack.invalid.add(version.id)
    return verstack

def _deep_inspection(version: VersionDantic, verstack: VerStack, skip: set[str] | None = None) -> bool:

    if skip is None:
        skip = set()

    for dep_id in version.dependencies:

        if dep_id in skip:
            continue

        if dep_id in verstack.invalid:
            return False

        if dep_id in version.parsed_deps.keys():
            continue

        try:
            dependency = verstack.valid[dep_id]
            version.parsed_deps[dep_id] = dependency
            if dependency.dependencies:
                if not _deep_inspection(dependency, verstack, skip):
                    return False
        except KeyError:
            return False
        skip.add(dep_id)
    return True

def _update_dep_list(dep_list: set[str], verstack: VerStack) -> set[str]:
    for ver in verstack.valid.values():
        dep_list.update(ver.dependencies)
    return dep_list