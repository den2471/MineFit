from contextlib import asynccontextmanager
from fastapi import FastAPI
from httpx import AsyncClient, Limits
from pydantic import BaseModel

from src.modrinth.api_interface import request_projects, request_versions
from src.modrinth.validation import Project, Version
from src.util import segment

class ProjectsIds(BaseModel):
    ids: set[str]

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