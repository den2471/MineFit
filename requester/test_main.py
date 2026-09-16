from src.modrinth.api_interface import request_versions
from asyncio import run
from httpx import AsyncClient

print(
    run(request_versions(
            [['NqwNSxwA']], AsyncClient()
        )
    )
)