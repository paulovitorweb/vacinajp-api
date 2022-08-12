import asyncio
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from src.vacinajp.api.main import app


@pytest_asyncio.fixture()
async def test_app():
    """
    Create an instance of the client.
    :return: yield HTTP client.
    """
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://127.0.0.1:8000", follow_redirects=True) as ac:
            yield ac


@pytest_asyncio.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()