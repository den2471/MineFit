from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

from src.external.requester import get_projects

class ProjectsIds(BaseModel):
    ids: set[str]

app = FastAPI()

@app.post('/game_versions')
async def calculate_versions(id_list: ProjectsIds):
    
    return