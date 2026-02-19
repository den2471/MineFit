from typing import Collection, overload

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from src.utility import log

from src.schemas import *
import asyncio

class VerStack:
    def __init__(self) -> None:
        self.parsed: dict[str, VersionDantic] = {}
        self.invalid: dict[str,InvalidVersionDantic] = {}

engine = create_async_engine('sqlite+aiosqlite:///cache/modrinth.db', echo=False)
Session = async_sessionmaker(engine)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(BaseORM.metadata.create_all)
    await engine.dispose()

asyncio.run(init_db())

async def enrich_ver_stack(ids: Collection[str] | str, ver_stack: VerStack) -> None:

    """
    Pulls, validates versions from db and enrich versions stack.

    """
    
    if not isinstance(ids, Collection):
        ids = [ids]

    async with Session() as session:

        parsed_stmt = select(VersionORM).where(VersionORM.id.in_(ids))
        invalid_stmt = select(InvalidVersionORM).where(InvalidVersionORM.id.in_(ids))

        parsed_result = await session.scalars(parsed_stmt)
        invalid_result = await session.scalars(invalid_stmt)

        parsed_orm = parsed_result.all()
        invalid_orm = invalid_result.all()

        for ver in parsed_orm:
            model = VersionDantic.model_validate(ver)
            ver_stack.parsed[model.id] = model

        for ver in invalid_orm:
            model = InvalidVersionDantic.model_validate(ver)
            ver_stack.invalid[model.id] = model

async def _dantic_to_orm(data: list[VersionDantic | InvalidVersionDantic]) -> list[VersionORM | InvalidVersionORM]:

    result = []

    for obj in data:
        if isinstance(obj, VersionDantic):
            result.append(VersionORM(**obj.model_dump()))
        else:
            result.append(InvalidVersionORM(**obj.model_dump()))

    return result

async def add_versions_to_session(session: AsyncSession, data_dantic: VersionDantic | InvalidVersionDantic | list[VersionDantic | InvalidVersionDantic] | None) -> None:

    if not data_dantic:
        return

    if not isinstance(data_dantic, Collection):
        data_dantic = [data_dantic]

    data_orm = await _dantic_to_orm(data_dantic)

    session.add_all(data_orm)

    log(f'Added data to session')

async def commit_changes(session: AsyncSession) -> None:

    await session.flush()
    await session.commit()

    log(f'Commit done')