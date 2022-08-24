from pydantic import BaseSettings


class Settings(BaseSettings):
    environment: str = 'local'
    mongo_connection: str = "mongodb://localhost:27017"
    mongo_db: str = "vacinajp"
    jwt_token_expire: int = 30
    jwt_secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # temp
    admin_username: str = "jon-snow"  # temp
    admin_password: str = "you-know-nothing"  # temp
