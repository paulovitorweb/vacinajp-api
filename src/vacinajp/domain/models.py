import datetime
from typing import Generic, List, Tuple, TypeVar, Optional

import pymongo
from beanie import Document, PydanticObjectId
from pydantic import BaseModel


T = TypeVar("T")


class Address(BaseModel):
    street_name: str
    street_number: int
    neighborhood: str


class GeoJson2DPoint(BaseModel):
    type: str = "Point"
    coordinates: Tuple[float, float]


class VaccinacionSite(Document):
    name: str
    address: Address
    geo: GeoJson2DPoint

    class Settings:
        name = "vaccination_sites"
        indexes = [
            [("geo", pymongo.GEOSPHERE)],
        ]


class Calendar(Document):
    date: datetime.date
    vaccination_site: PydanticObjectId
    total_schedules: int  # Total ofertado para este local
    remaining_schedules: int  # Total disponível
    is_available: bool

    class Settings:
        name = "calendar"
        indexes = [
            "date_vaccination_site",
            [
                ("date", pymongo.ASCENDING),
                ("vaccination_site", pymongo.ASCENDING),
            ]
        ]
        bson_encoders = {
            datetime.date: lambda dt: datetime.datetime(year=dt.year, month=dt.month, day=dt.day, hour=0, minute=0, second=0)
        }


class User(Document):
    name: str

    class Settings:
        name = "users"


class Vaccine(Document):
    user: PydanticObjectId
    date: datetime.date
    vaccination_site: PydanticObjectId
    dose: int
    laboratory: str = "Pfizer"
    vaccination_site_name: str = None

    class Settings:
        name = "vaccines"
        indexes = [
            [("user", pymongo.ASCENDING)],
        ]
        bson_encoders = {
            datetime.date: lambda dt: datetime.datetime(year=dt.year, month=dt.month, day=dt.day, hour=0, minute=0, second=0)
        }


class Schedule(Document):
    user: PydanticObjectId
    date: datetime.date
    vaccination_site: PydanticObjectId
    vaccination_site_name: str = None
    user_attended: bool = False
    vaccine: Optional[PydanticObjectId] = None

    class Settings:
        name = "schedules"
        indexes = [
            [("user", pymongo.ASCENDING)],
        ]
        bson_encoders = {
            datetime.date: lambda dt: datetime.datetime(year=dt.year, month=dt.month, day=dt.day, hour=0, minute=0, second=0)
        }


class UserInfo(User):
    vaccine_card: List[Vaccine]
    schedules: List[Schedule]


class Paged(Generic[T]):
    items: List[T]
    size: int
    more_pages: bool

    def __init__(self, number: int, items: List[T], more_pages: bool):
        self.items = items
        self.number = number
        self.more_pages = more_pages


__beanie_models__ = [VaccinacionSite, Calendar, Schedule, Vaccine, User]