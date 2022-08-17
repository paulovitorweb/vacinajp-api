from typing import Optional
from hmac import compare_digest
from beanie import PydanticObjectId
from fastapi import HTTPException, Depends, Security, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBasicCredentials,
    HTTPBearer,
    HTTPBasic,
)
from pydantic import BaseModel
from jose import JWTError

from src.vacinajp.common.config import Settings
from src.vacinajp.common.helpers import JwtHelper
from src.vacinajp.infrastructure.mongo_client import client
from src.vacinajp.domain.models import UserInfo, UserRole


settings = Settings()


class TokenData(BaseModel):
    user_id: Optional[str] = None


async def get_current_user(authorization: HTTPAuthorizationCredentials = Security(HTTPBearer())):
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


async def get_current_professional_user(user_info: UserInfo = Depends(get_current_user)):
    if UserRole.HEALTHCARE_PROFESSIONAL not in user_info.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have the role required to access this feature",
        )
    return user_info


async def get_current_operator_user(user_info: UserInfo = Depends(get_current_user)):
    if UserRole.OPERATOR not in user_info.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have the role required to access this feature",
        )
    return user_info


async def check_admin_access(credentials: HTTPBasicCredentials = Security(HTTPBasic())):
    if credentials.username == settings.admin_username and compare_digest(
        credentials.password, settings.admin_password
    ):
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
    )
