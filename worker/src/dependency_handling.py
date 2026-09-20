from collections import deque, defaultdict

import src.pull_from as pull_from
from src.data.schemas import VerStack

async def main_pipeline(verstack: VerStack, pull_from = pull_from) -> VerStack:

    to_collect_deps = set(verstack.valid)

    while to_collect_deps:

        dep_list = _get_missing_dependencies(to_collect_deps, verstack)
        
        if dep_list:

            verstack, remain = await pull_from.local_cache(dep_list, verstack)
            
            if remain:
                verstack, remain = await pull_from.db(remain, verstack)           
        
            if remain:
                verstack = await pull_from.api(remain, verstack)
        else:
            break

        to_collect_deps = dep_list

    verstack = _enrich_versions_with_deps(verstack)
    verstack = _discard_invalid(verstack)
    return verstack

def _get_missing_dependencies(ver_id_list: set[str], verstack: VerStack) -> set[str]:
    resolved = verstack.valid.keys() | verstack.invalid
    missing_deps = set()

    for ver_id in ver_id_list:
        if ver := verstack.valid.get(ver_id):
            for dep_id in ver.dependencies:
                if dep_id not in resolved:
                    missing_deps.add(dep_id)
    return missing_deps

def _discard_invalid(verstack: VerStack) -> VerStack:

    dependendants_map: dict[str, set[str]] = defaultdict(set)
    to_delete = deque()
    hashed_to_delete = set()

    for ver_id, ver in verstack.valid.items():
        for dep_id in ver.dependencies:
            dependendants_map[dep_id].add(ver_id)
            if dep_id not in verstack.valid and ver_id not in hashed_to_delete:
                to_delete.append(ver_id)
                hashed_to_delete.add(ver_id)

    while to_delete:

        ver_id = to_delete.popleft()
        hashed_to_delete.remove(ver_id)

        if ver_id in verstack.valid:
            verstack.valid.pop(ver_id)
            verstack.invalid.add(ver_id)

            for parent_id in dependendants_map[ver_id]:
                if parent_id in verstack.valid and parent_id not in hashed_to_delete:
                    to_delete.append(parent_id)
                    hashed_to_delete.add(parent_id)

    return verstack

def _enrich_versions_with_deps(verstack: VerStack) -> VerStack:

    for ver in verstack.valid.values():
        for dep_id in ver.dependencies:
            ver.parsed_deps[dep_id] = verstack.valid[dep_id]

    return verstack