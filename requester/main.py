from contextlib import asynccontextmanager
from fastapi import FastAPI
from httpx import AsyncClient, Limits
from pydantic import BaseModel, field_validator
from re import compile

from src.modrinth.api_interface import request_projects, request_versions
from src.modrinth.validation import Project, Version
from src.util import segment

class ProjectsIds(BaseModel):
    ids: set[str]
    ID_SLUG = compile(r"^[A-Za-z0-9_.-]{3,64}$")
    @field_validator('ids')
    @classmethod
    def validate_ids(cls, ids: set[str]) -> set[str]:
        if len(ids) == 0:
            raise ValueError('No ids presented')
        if len(ids) > 200:
            raise ValueError('Too many ids presented. Id cap is 200')
        for id in ids:
            if not cls.ID_SLUG.match(id):
                raise ValueError('Wrong id presented')
        return ids

@asynccontextmanager
async def lifespan(app: FastAPI):
    limiter = Limits(max_connections=20)
    async with AsyncClient(limits=limiter) as client:
        app.state.client = client
        yield

app = FastAPI()

@app.post('/modrinth/projects')
async def get_projects(body: ProjectsIds):
    segmented = segment(body.ids)
    responce = await request_projects(segmented, app.state.client)

    validated = {}
    for proj in responce:
        model = Project.model_validate(proj)
        validated[proj['id']] = model.model_dump()
    return validated
    
@app.post('/modrinth/versions')
async def get_versions(body: ProjectsIds):
    segmented = segment(body.ids)
    responce = await request_versions(segmented, app.state.client)

    validated = {}
    for proj in responce:
        model = Version.model_validate(proj)
        validated[proj['id']] = model.model_dump()
    return validated