from src.external import _db, _local_cache
from src.data.schemas import VerStack, InvalidVersionORM
from src.external import _requester
from src.util import _clean_id_list

async def local_cache(id_list: set[str], main_verstack: VerStack) -> tuple[VerStack, set[str]]:
    cached_verstack = await _local_cache.get_versions(id_list)
    remain = _clean_id_list(id_list, cached_verstack)
    main_verstack.merge(cached_verstack)
    return main_verstack, remain

async def db(id_list: set[str], main_verstack: VerStack) -> tuple[VerStack, set[str]]:
    stored_verstack = await _db.get_versions(id_list)
    remain = _clean_id_list(id_list, stored_verstack)
    main_verstack.merge(stored_verstack)
    return main_verstack, remain

async def api(id_list: set[str], main_verstack: VerStack) -> VerStack:
    requested_verstack = await _requester.get_versions(id_list)
    remain = _clean_id_list(id_list, requested_verstack)
    if remain:
        requested_verstack.invalid.update(remain)
    main_verstack.merge(requested_verstack)
    if requested_verstack.invalid:
        await _db.push_versions([InvalidVersionORM(id=id) for id in requested_verstack.invalid])
    return main_verstack