import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from beanie import PydanticObjectId

from src.vacinajp.infrastructure.mongo_repository import MongoUnitOfWork
from src.vacinajp.domain.models import User, UserInfo, UserRole
from src.vacinajp.common.helpers import JwtHelper, SecurityHelper
from src.vacinajp.common.errors import UserAlreadyExists
from src.vacinajp.api.dependencies import get_current_user, get_uow


users_router = APIRouter()


class ExceptionDetail(BaseModel):
    detail: str


class CreateUser(BaseModel):
    name: str
    cpf: str
    birth_date: datetime.date


class UserOut(BaseModel):
    id: PydanticObjectId = Field(alias='_id')
    name: str
    cpf: str
    birth_date: datetime.date
    roles: List[UserRole]


class Token(BaseModel):
    access_token: str
    token_type: str


class BaseUserLogin(BaseModel):
    cpf: str


class BasicUserLogin(BaseUserLogin):
    birth_date: datetime.date


class UserLoginWithPassword(BaseUserLogin):
    password: str


login_responses = {
    401: {"model": ExceptionDetail},
    403: {"model": ExceptionDetail},
    404: {"model": ExceptionDetail},
}


@users_router.post(
    "/",
    response_model=UserOut,
    status_code=201,
    responses={409: {"model": ExceptionDetail}},
)
async def create_user(user: CreateUser, uow: MongoUnitOfWork = Depends(get_uow)):
    async with uow():
        user = User(**user.dict())
        try:
            user = await uow.users.create(user)
        except UserAlreadyExists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='User with provided cpf already exists',
            )
        return user


@users_router.post(
    "/login",
    response_model=Token,
    status_code=200,
    responses=login_responses,
)
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


@users_router.post(
    "/login/staff",
    response_model=Token,
    status_code=200,
    responses=login_responses,
)
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


@users_router.get(
    "/me",
    response_model=UserInfo,
    status_code=200,
    responses={401: {"model": ExceptionDetail}},
)
async def read_users_me(current_user: UserInfo = Depends(get_current_user)):
    return current_user
