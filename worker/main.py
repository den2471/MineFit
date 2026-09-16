from re import compile
from fastapi import FastAPI
from pydantic import BaseModel, field_validator
from projects_handling import main_pipeline

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

app = FastAPI()

@app.post('/game_versions')
async def calculate_versions(id_list: ProjectsIds):
    respond = await main_pipeline(id_list.ids)
    return