from typing import Optional
from beanie import PydanticObjectId
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from jose import JWTError

from src.vacinajp.common.helpers import JwtHelper
from src.vacinajp.infrastructure.mongo_client import client


security = HTTPBearer()


class TokenData(BaseModel):
    user_id: Optional[str] = None


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
