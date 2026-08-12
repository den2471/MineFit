from pydantic import ValidationError
from typing import Any

from src.data.schemas import ProjectDantic, VersionDantic, VerStack, ProjStack

def projects_from_api(raw_data: list[dict]) -> ProjStack:
    projstack = ProjStack()
    for row in raw_data:
        try:
            model = ProjectDantic.model_validate(row)
            projstack.valid[model.id] = model
        except ValidationError:
            try:
                projstack.invalid.add(row['id'])
            except KeyError:
                pass
    return projstack

def versions_from_cache(raw_data: list[Any]) -> VerStack:
    verstack = VerStack()
    for row in raw_data:
        if isinstance(row, dict):
            try:
                model = VersionDantic.model_validate(raw_data)
                verstack.valid[model.id] = model
            except ValidationError:
                try:
                    verstack.invalid.add(row['id'])
                except KeyError:
                    pass
    return verstack

def versions_from_api(raw_data: list[dict]) -> VerStack:
    verstack = VerStack()
    for row in raw_data:
        try:
            model = VersionDantic.model_validate(row)
            verstack.valid[model.id] = model
        except ValidationError:
            try:
                verstack.invalid.add(row['id'])
            except KeyError:
                pass
    return verstack