from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, field_validator

import re

class ProjectTree(BaseModel):
    ...

class ProjectDantic(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    body: str
    client_side: str
    server_side: str
    project_type: str
    game_versions: set[str]
    loaders: set[str]
    versions: set[str]
    parsed_versions: dict[str, 'VersionDantic'] = {}
    invalid_versions: set[str]
    updated: str

    model_config = {
        "from_attributes": True
    }

class InvalidProjectDantic(BaseModel):
    id: str

    model_config = {
        "from_attributes": True
    }

class VersionDantic(BaseModel):
    id: str
    name: str
    dependencies: set[str]
    parsed_deps: dict[str, 'VersionDantic'] = {}
    game_versions: set[str]
    version_type: str
    loaders: set[str]
    status: str
    date_published: str
    project_id: str
    
    model_config = {
        "from_attributes": True
    }

    @field_validator('dependencies', mode='before')
    @classmethod
    def deps_to_str(cls, data: list[dict] | list) -> list:

        if not data:
            return []
        
        if isinstance(data[0], str):
            return data

        result = []
        for dep in data:
            try:
                result.append(dep['version_id'])
            except KeyError:
                pass
        return result 

class VerStack(BaseModel):
    valid: dict[str, VersionDantic] = {}
    invalid: set[str] = set()

    def merge(self, verstack: 'VerStack'):
        self.valid.update(verstack.valid)
        self.invalid.update(verstack.invalid)

class ProjStack(BaseModel):
    valid: dict[str, ProjectDantic] = {}
    invalid: set[str] = set()

BaseORM = declarative_base()

class VersionORM(BaseORM):

    __tablename__ = 'versions'

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String
    )

    dependencies: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    game_versions: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    version_type: Mapped[str] = mapped_column(
        String
    )

    loaders: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String
    )

    date_published: Mapped[str] = mapped_column(
        String
    )

    project_id: Mapped[str] = mapped_column(
        String
    )

class InvalidVersionORM(BaseORM):

    __tablename__ = 'invalid_versions'

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
    )

SINGLE_URL = re.compile(r'^https://modrinth\.com/(shader|resourcepack|mod)/[\w-]+$')

class ProjectList(BaseModel):

    urls: list[str]

    @field_validator('urls')
    @classmethod
    def validate_links(cls, url_list: list[str]):
        for url in url_list:
            if not SINGLE_URL.match(url):
                raise ValueError(f'"{url}" is not Modrinth project. Please check if url is valid.')
        return url_list