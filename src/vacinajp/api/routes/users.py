import datetime
from typing import Optional
from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Security, Depends, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import JWTError
from pydantic import BaseModel

from src.vacinajp.infrastructure.mongo_client import client
from src.vacinajp.domain.models import UserInfo
from src.vacinajp.common.helpers import JwtHelper, SecurityHelper


users_router = APIRouter()
security = HTTPBearer()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


class BaseUserLogin(BaseModel):
    cpf: str


class BasicUserLogin(BaseUserLogin):
    birth_date: datetime.date


class UserLoginWithPassword(BaseUserLogin):
    password: str


@users_router.post("/login", response_model=Token)
async def basic_login(login: BasicUserLogin):
    async with client.start_transaction() as repo:
        user = await repo.get_user_from_cpf(login.cpf)

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
async def staff_login(login: UserLoginWithPassword):
    async with client.start_transaction() as repo:
        user = await repo.get_user_from_cpf(cpf=login.cpf)

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


async def get_current_user(authorization: HTTPAuthorizationCredentials = Security(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
    )
    try:
        payload = JwtHelper.decode_access_token(authorization.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    async with client.start_transaction() as repo:
        user_info = await repo.get_user_info(PydanticObjectId(token_data.user_id))
    if user_info is None:
        raise credentials_exception
    return user_info


@users_router.get("/me", response_model=UserInfo)
async def read_users_me(current_user: UserInfo = Depends(get_current_user)):
    return current_user
