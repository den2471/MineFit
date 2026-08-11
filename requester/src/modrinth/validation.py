from pydantic import BaseModel, field_validator

class Project(BaseModel):
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
    updated: str

class Version(BaseModel):
    id: str
    name: str
    dependencies: list[str]
    game_versions: list[str]
    version_type: str
    loaders: list[str]
    status: str
    date_published: str
    project_id: str

    @field_validator('dependencies', mode='before')
    @classmethod
    def dependencies_validate(cls, dep_list: list[dict]):
        return [version['version_id'] for version in dep_list]