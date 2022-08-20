import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from src.vacinajp.infrastructure.mongo_repository import MongoUnitOfWork
from src.vacinajp.domain.models import User, UserInfo
from src.vacinajp.common.helpers import JwtHelper, SecurityHelper
from src.vacinajp.api.dependencies import get_current_user, get_uow


users_router = APIRouter()


class CreateUser(BaseModel):
    name: str
    cpf: str
    birth_date: str


class Token(BaseModel):
    access_token: str
    token_type: str


class BaseUserLogin(BaseModel):
    cpf: str


class BasicUserLogin(BaseUserLogin):
    birth_date: datetime.date


class UserLoginWithPassword(BaseUserLogin):
    password: str


@users_router.post("/")
async def create_user(user: CreateUser, uow: MongoUnitOfWork = Depends(get_uow)):
    async with uow():
        user = User(**user.dict())
        try:
            user = await uow.users.create(user)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='User with provided cpf already exists',
            )


@users_router.post("/login", response_model=Token)
async def basic_login(login: BasicUserLogin, uow: MongoUnitOfWork = Depends(get_uow)):
    async with uow():
        user = await uow.users.get_from_cpf(login.cpf)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

        if user.birth_date != login.birth_date:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized user'
            )

        if user.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden access')

        access_token = JwtHelper.create_access_token(data={"sub": str(user.id)})

        return {"access_token": access_token, "token_type": "bearer"}


@users_router.post("/login/staff", response_model=Token)
async def staff_login(login: UserLoginWithPassword, uow: MongoUnitOfWork = Depends(get_uow)):
    async with uow():
        user = await uow.users.get_from_cpf(login.cpf)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

        if not SecurityHelper.verify_password(login.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Unauthorized user. Incorrent credentials.',
            )

        if not user.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden access')

        access_token = JwtHelper.create_access_token(data={"sub": str(user.id)})

        return {"access_token": access_token, "token_type": "bearer"}


@users_router.get("/me", response_model=UserInfo)
async def read_users_me(current_user: UserInfo = Depends(get_current_user)):
    return current_user
