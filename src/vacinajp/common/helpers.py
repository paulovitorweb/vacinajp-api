import string
import secrets
from datetime import datetime, timedelta
from passlib.context import CryptContext

from jose import jwt

from src.vacinajp.common.config import Settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = Settings()


class SecurityHelper:
    @staticmethod
    def verify_password(plain_password, hashed_password) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def generate_safe_password() -> str:
        password_length = 13
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(password_length))
        return password


class JwtHelper:
    @staticmethod
    def create_access_token(data: dict) -> str:
        to_encode = data.copy()
        expire = DateHelper.utcnow() + timedelta(minutes=settings.jwt_token_expire)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm="HS256")
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> dict:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])


class DateHelper:
    @staticmethod
    def utcnow() -> datetime:
        return datetime.utcnow()
