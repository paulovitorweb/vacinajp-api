import asyncio
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from src.vacinajp.api.main import app
from src.vacinajp.infrastructure.mongo_client import client as mongo_client

from .fake_db import get_fake_calendar, get_fake_vaccination_sites


@pytest_asyncio.fixture()
async def test_app():
    """
    Create an instance of the client.
    :return: yield HTTP client.
    """
    async with LifespanManager(app):
        async with AsyncClient(
            app=app, base_url="http://127.0.0.1:8000", follow_redirects=True
        ) as ac:
            yield ac


@pytest_asyncio.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True, scope="session")
async def db_test():
    db = mongo_client.db
    result = await db['vaccination_sites'].insert_many(get_fake_vaccination_sites())
    await db['calendar'].insert_many(get_fake_calendar(result.inserted_ids))
    yield db
    for collection in await db.list_collection_names():
        await db[collection].delete_many({})


@pytest_asyncio.fixture()
async def session_test():
    await mongo_client.initialize()
    async with mongo_client.start_session() as session:
        yield session
