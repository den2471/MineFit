from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel, field_validator
from typing import Optional
import re

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
    parsed_versions: list[VersionORM] = []
    invalid_versions: list[InvalidVersionORM] = []
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
    name: str
    dependencies: list[str]
    game_versions: list[str]
    version_type: str
    loaders: list[str]
    status: str
    id: str
    date_published: str
    project_id: str
    
    child: bool = False

    model_config = {
        "from_attributes": True
    }
    
class InvalidVersionDantic(BaseModel):
    id: str
    project_id: str

    model_config = {
        "from_attributes": True,
        'extra': 'ignore'
    }

class ProjectsList(BaseModel):
    text: str

    @field_validator('text')
    def validate_links(cls, text: str):

        SINGLE_URL = re.compile(f'https://modrinth.com/(shader|resourcepack|mod)/')

        rows = text.splitlines()
        
        for row in rows:
            matches = SINGLE_URL.findall(row)
            if not row:
                continue
            if len(matches) > 1 or len(matches) < 1:
                raise ValueError
        
        return text