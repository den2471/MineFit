from typing import Collection, overload

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from src.schemas import *
import asyncio

engine = create_async_engine('sqlite+aiosqlite:///cache/modrinth.db', echo=False)
Session = async_sessionmaker(engine)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(BaseORM.metadata.create_all)
    await engine.dispose()

asyncio.run(init_db())

async def get_versions(ids: Collection[str] | str) -> tuple[Collection[VersionORM], Collection[InvalidVersionORM]]:
    
    async with Session() as session:

        if not isinstance(ids, Collection):
            ids = [ids]

        parsed_stmt = select(VersionORM).where(VersionORM.id.in_(ids))
        invalid_stmt = select(InvalidVersionORM).where(InvalidVersionORM.id.in_(ids))

        parsed_result = await session.scalars(parsed_stmt)
        invalid_result = await session.scalars(invalid_stmt)

        return parsed_result.all(), invalid_result.all()

async def save_versions(data: VersionORM | InvalidVersionORM | Collection[VersionORM | InvalidVersionORM]) -> None:

    if not isinstance(data, Collection):
        data = [data]

    async with Session() as session:
        session.add_all(data)

async def commit_changes() -> None:
    async with Session() as session:
        await session.flush()
        await session.commit()