from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from src.data.schemas import VersionORM, InvalidVersionORM, VerStack, VersionDantic
from util import settings

engine = create_async_engine(f'postgresql+asyncpg://worker:{settings.DB_PASS}@{settings.DB_HOST}:5432/vault', echo=False)
Session = async_sessionmaker(engine)

async def get_versions(id_list: set[str]) -> VerStack:

    verstack = VerStack()

    async with Session() as session:
        raw_versions = await session.execute(select(VersionORM).where(VersionORM.id.in_(id_list)))
        raw_inv_versions = await session.execute(select(InvalidVersionORM).where(InvalidVersionORM.id.in_(id_list)))
        versions = raw_versions.scalars().all()
        inv_versions = raw_inv_versions.scalars().all()
        for ver in versions:
            verstack.valid[ver.id] = VersionDantic.model_validate(ver)
        for inv_ver in inv_versions:
            verstack.invalid.update(inv_ver)
    return verstack

async def push_versions(data: list[VersionORM | InvalidVersionORM]) :
    async with Session() as session:
        try:
            session.add_all(data)
            await session.commit()
        except Exception as ex:
            await session.rollback()
            raise ex