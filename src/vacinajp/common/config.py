from pydantic import BaseSettings


class Settings(BaseSettings):
    mongo_connection: str = "mongodb://localhost:27017"
    mongo_db = "vacinajp"
