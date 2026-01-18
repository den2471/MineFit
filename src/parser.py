import requests
from schemas import ProjectDantic
from utility import *
from pydantic import ValidationError
from ver_repo import *
import re
from typing import TypeAlias
from collections import defaultdict


FlatProjects: TypeAlias = dict[
    str, dict[
        str, dict[
            str, tuple[
                ProjectDantic, 
                VersionDantic
            ]
        ]
    ]
]

class ProjectStack:
    
    def __init__(self) -> None:
        self.mods: list[ProjectDantic] = []
        self.shaders: list[ProjectDantic] = []
        self.resources: list[ProjectDantic] = []

        self.title_index: dict[str, str] = {}

    def flat_projects(self, project_list: list[ProjectDantic]) -> FlatProjects:
        '''
        Bulds projects index

        :param project_list: List of parsed projects
        :type project_list: list[ProjectDantic]
        :return: Projects index in the following format: project_slug -> loader -> game_version -> (project_dantic, version_dantic)
        :rtype: FlatProjects
        '''
        index: FlatProjects = defaultdict(lambda: defaultdict(dict))

        for project in project_list:
            self.title_index[project.id] = project.title
            for ver_dantic in project.parsed_versions:
                for loader in ver_dantic.loaders:
                    for game_ver in ver_dantic.game_versions:
                        index[loader][project.id][game_ver] = (project, ver_dantic)

        def freeze(obj):
            if isinstance(obj, dict):
                return {k: freeze(v) for k, v in obj.items()}
            return obj 
            
        return freeze(index)

project_stack = ProjectStack()

class Modrinth:

    project_api_url = 'https://api.modrinth.com/v2/project/[id]'

    @classmethod
    def parse_project(cls, url: str) -> ProjectDantic | None:
        
        if re.match(f'https://modrinth.com/(mod|shader|resourcepack)/.*', url):

            _, slug = url.rsplit('/', 1)

            project_endpoint = concatenate_endpoint(cls.project_api_url, slug)
            try:
                response = requests.get(project_endpoint)
                json_responce = response.json()
                json_responce['url'] = url
                project = ProjectDantic.model_validate(json_responce)
                cprint(f'Project {project.title}', end='\n')
                for version_id in project.versions:
                    ver = VerRepo.get(version_id)
                    if ver:
                        project.parsed_versions.append(ver)

                if project.versions:
                    if project.project_type == 'mod':
                        project_stack.mods.append(project)
                    if project.project_type == 'resourcepack':
                        project_stack.resources.append(project)
                    if project.project_type == 'shader':
                        project_stack.shaders.append(project)
                    
            except ValidationError:
                cprint(f'Modrinth - Wrong api responce', color=pcolor.error, end='\n')
                return
            except Exception as ex:
                cprint(f'Modrinth - Exception\n{ex}', color=pcolor.error, end='\n')
        else:
            cprint(f'Invalid project url', color=pcolor.error, end='\n')


if __name__ == '__main__':
    project_list = open('projects.txt', 'r').read().split('\n')
    for project_url in project_list:
        project = Modrinth.parse_project(project_url)

    mods = project_stack.flat_projects(project_stack.mods)
    shaders = project_stack.flat_projects(project_stack.shaders)
    resources = project_stack.flat_projects(project_stack.resources)

    print(mods.items())