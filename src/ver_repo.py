import requests
from utility import *
from schemas import *
from cache import session
from sqlalchemy import select
from pydantic import ValidationError

class VerRepo:

    @classmethod
    def add(cls, slug: str) -> VersionDantic | None:
        try:
            versions_api_url = 'https://api.modrinth.com/v2/version/[id]'
            version_endpoint = concatenate_endpoint(versions_api_url, slug)
            responce = requests.get(version_endpoint).json()

            _dep_list = []
            for _dep in responce['dependencies']:
                if (_dep['dependency_type'] == 'required' or _dep['dependency_type'] == 'optional') and _dep['version_id'] is not None:
                    _dep_list.append(_dep['version_id'])
                elif _dep['version_id'] is None or _dep['project_id'] is None or _dep['file_name'] is None:
                    cprint('invalid', color=pcolor.error, end='\n')
                    session.add(InvalidVersionORM(id=slug))
                    session.flush()
                    session.commit()
                    return None
            responce['dependencies'] = _dep_list

            ver_dantic = VersionDantic.model_validate(responce)
            model_dumped = ver_dantic.model_dump()
            ver_orm = VersionORM(**model_dumped)

            session.add(ver_orm)
            session.flush()
            session.commit()

            cprint('done', color=pcolor.success, end='\n')

            cls.dep_check(ver_dantic)

            return ver_dantic
        except ValidationError as ex:
            cprint('validation error', color=pcolor.error, end='\n')
            print(ex)
            return None
        
    @classmethod
    def get(cls, slug: str) -> VersionDantic | None:
        statement = select(VersionORM).filter_by(id=slug)
        chaced_ver = session.scalars(statement).one_or_none()

        statement = select(InvalidVersionORM).filter_by(id=slug)
        invalid_ver = session.scalars(statement).one_or_none()

        if chaced_ver:
            cprint(f'Using cached ver {slug} ', end='\n', color=pcolor.success)
            return chaced_ver
        elif invalid_ver:
            cprint(f'{slug} cached as invalid', end='\n', color=pcolor.error)
            return None
        else:
            cprint(f'Caching ver {slug} ')
            return cls.add(slug)
        
    @classmethod
    def dep_check(cls, ver: VersionDantic) -> None:
        for dep_slug in ver.dependencies:
            cprint(f'Dependency ', pcolor.disabled)
            dep = cls.get(dep_slug)