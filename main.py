from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from src.schemas import ProjectsList
from src.parser import Modrinth

import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get('/')
async def main(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.post('/projects')
async def projects(data: ProjectsList):
    result = await Modrinth.parse_projects(data.text)
    return {'status': 'ok', 'data': json.dumps(result)}