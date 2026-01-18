import requests
from utility import *
from schemas import *
from cache import session
from sqlalchemy import select
from pydantic import ValidationError

class VerRepo:

    @classmethod
    def add(cls, version_id: str, project_id: str) -> VersionDantic | None:
        try:
            versions_api_url = 'https://api.modrinth.com/v2/version/[id]'
            version_endpoint = concatenate_endpoint(versions_api_url, version_id)
            responce = requests.get(version_endpoint).json()

            dependency_list = []
            for dependency in responce['dependencies']:
                if dependency['version_id'] is None or dependency['project_id'] is None or dependency['file_name'] is None:
                    cprint('invalid', color=pcolor.error, end='\n')
                    session.add(InvalidVersionORM(id=version_id, project_id=project_id))
                    session.flush()
                    session.commit()
                    return None
                if (dependency['dependency_type'] == 'required' or dependency['dependency_type'] == 'optional') and dependency['version_id'] is not None:
                    dependency_list.append(dependency['version_id'])

            responce['dependencies'] = dependency_list

            ver_dantic = VersionDantic.model_validate(responce)
            model_dumped = ver_dantic.model_dump()
            ver_orm = VersionORM(**model_dumped)

            session.add(ver_orm)
            session.flush()
            session.commit()

            cprint('done', color=pcolor.success, end='\n')

            cls.dependency_check(ver_dantic)

            return ver_dantic
        
        except ValidationError as ex:
            cprint('validation error', color=pcolor.error, end='\n')
            print(ex)
            return None
        
    @classmethod
    def get(cls, version_id: str, project_id: str) -> VersionDantic | None:
        statement = select(VersionORM).filter_by(id=version_id)
        cached_ver = session.scalars(statement).one_or_none()

        statement = select(InvalidVersionORM).filter_by(id=version_id)
        invalid_ver = session.scalars(statement).one_or_none()

        if cached_ver:
            return cached_ver
        elif invalid_ver:
            return None
        else:
            cprint(f'Caching ver {version_id} ')
            return cls.add(version_id, project_id)
        
    @classmethod
    def dependency_check(cls, ver: VersionDantic) -> None:
        for dependency_id in ver.dependencies:
            cprint(f'Dependency ', pcolor.disabled)
            cls.get(dependency_id, ver.project_id)

    @classmethod
    def check_cached(cls, project_id: str) -> tuple[int, int]:
        statement = select(VersionORM).filter_by(project_id=project_id)
        cached_ver = session.scalars(statement).all()

        statement = select(InvalidVersionORM).filter_by(project_id=project_id)
        invalid_ver = session.scalars(statement).all()
        return (len(cached_ver), len(invalid_ver))