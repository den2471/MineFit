import requests
from schemas import VersionORM, ProjectDantic
from utility import *
from pydantic import ValidationError
from ver_repo import *

class Modrinth:

    project_api_url = 'https://api.modrinth.com/v2/project/[id]'

    @classmethod
    def parse_project(cls, url: str) -> ProjectDantic | None:
        
        type, slug = url.rsplit('/', 1)
        type = type.rsplit('/', 1)[-1]
        if type == 'mod':

            project_endpoint = concatenate_endpoint(cls.project_api_url, slug)
            try:
                response = requests.get(project_endpoint)
                json_responce = response.json()
                json_responce['url'] = url
                project = ProjectDantic.model_validate(json_responce)
                cprint(f'Project {project.title}', end='\n')
                for version_id in project.versions:
                    version = VerRepo.get(version_id)

            except ValidationError:
                cprint(f'Modrinth - Wrong api responce', color=pcolor.error, end='\n')
                return
            except Exception as ex:
                cprint(f'Modrinth - Exception\n{ex}', color=pcolor.error, end='\n')

        elif type == 'resourcepack' or type == 'shader':
            pass
        else:
            cprint(f'Invalid project url', color=pcolor.error, end='\n')


if __name__ == '__main__':
    project_list = open('projects.txt', 'r').read().split('\n')
    for project_url in project_list:
        project = Modrinth.parse_project(project_url)