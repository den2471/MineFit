from src.parser import Modrinth
import asyncio

if __name__ == '__main__':
    projects = open('projects.txt', 'r').read()
    result = asyncio.run(Modrinth.parse_projects(projects))