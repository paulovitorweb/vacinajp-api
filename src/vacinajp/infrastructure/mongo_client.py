from contextlib import asynccontextmanager
from typing import AsyncIterator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession
from beanie import init_beanie

from src.vacinajp.common.config import Settings
from src.vacinajp.domain.models import __beanie_models__


class MongoClient:

    _client: AsyncIOMotorClient
    _database: str

    def __init__(self, connection_string: str, database: str) -> None:
        self._client = AsyncIOMotorClient(connection_string)
        self._database = database

    async def initialize(self) -> None:
        await init_beanie(database=self._client[self._database], document_models=__beanie_models__)

    @asynccontextmanager
    async def start_session(self) -> AsyncIterator[AsyncIOMotorClientSession]:
        async with await self._client.start_session() as session:
            yield session


settings = Settings()
client = MongoClient(settings.mongo_connection, settings.mongo_db)
