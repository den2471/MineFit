from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel, ConfigDict
from typing import Optional

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

    project_id: Mapped[str] = mapped_column(
        String
    )

class InvalidVersionORM(BaseORM):

    __tablename__ = 'invalid_versions'

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
    )

class ProjectDantic(BaseModel):
    url: str
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
    updated: str

class VersionDantic(BaseModel):
    name: str
    dependencies: list[str]
    game_versions: list[str]
    version_type: str
    loaders: list[str]
    status: str
    id: str
    project_id: str
    