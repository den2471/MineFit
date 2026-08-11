from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, field_validator

import re

class ProjectDantic(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    body: str
    client_side: str
    server_side: str
    project_type: str
    game_versions: list[str]
    loaders: list[str]
    versions: list[str]
    parsed_versions: list['VersionDantic'] = []
    invalid_versions: list['InvalidVersionDantic'] = []
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
    dependencies: list[str]
    game_versions: list[str]
    version_type: str
    loaders: list[str]
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
    
class InvalidVersionDantic(BaseModel):
    id: str

    model_config = {
        "from_attributes": True,
        'extra': 'ignore'
    }

class VerStack:
    def __init__(self) -> None:
        self.parsed: dict[str, VersionDantic] = {}
        self.invalid: dict[str,InvalidVersionDantic] = {}

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

    project_id: Mapped[str] = mapped_column(
        String
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