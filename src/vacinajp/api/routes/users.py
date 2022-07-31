from beanie import PydanticObjectId
from fastapi import APIRouter
from pydantic import BaseModel

from src.vacinajp.infrastructure.mongo_client import client
from src.vacinajp.domain.models import User


users_router = APIRouter()


class UserCreate(BaseModel):
    name: str


@users_router.get("/{user_id}")
async def get_user(user_id: PydanticObjectId):
    async with client.start_transaction() as repo:
        return await repo.get_user(user_id)


@users_router.post("/")
async def create_user(user: UserCreate):
    async with client.start_transaction() as repo:
        return await repo.create_user(User(**user.dict()))
