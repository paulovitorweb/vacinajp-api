import calendar
import random
import mimesis
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from beanie import PydanticObjectId

from src.vacinajp.domain.models import UserRole, VaccinacionSite, Calendar, Address, GeoJson2DPoint
from src.vacinajp.infrastructure.mongo_repository import MongoUnitOfWork
from src.vacinajp.common.helpers import SecurityHelper
from src.vacinajp.api.dependencies import check_admin_access, get_uow


admin_router = APIRouter()


class RoleToUser(BaseModel):
    roles: List[UserRole]


class PasswordToUser(BaseModel):
    password: str


@admin_router.patch("/users/{user_id}/roles")
async def set_role_to_user(
    user_id: PydanticObjectId,
    role_to_user: RoleToUser,
    _: bool = Depends(check_admin_access),
    uow: MongoUnitOfWork = Depends(get_uow),
):
    # this context doesn't have to be transactional because it's not multi-document
    async with uow():
        user = await uow.users.get(user_id)
        user.roles = role_to_user.roles
        await uow.users.update(user)


@admin_router.patch("/users/{user_id}/generate-password", response_model=PasswordToUser)
async def generate_password(
    user_id: PydanticObjectId,
    _: bool = Depends(check_admin_access),
    uow: MongoUnitOfWork = Depends(get_uow),
):
    # this context doesn't have to be transactional because it's not multi-document
    async with uow():
        user = await uow.users.get(user_id)
        password = SecurityHelper.generate_safe_password()
        hashed_password = SecurityHelper.get_password_hash(password)
        user.hashed_password = hashed_password
        await uow.users.update(user)
        return {'password': password}


@admin_router.post("/calendar/seed")
async def seed_calendar(
    year: int, month: int, schedules: int = 100, _: bool = Depends(check_admin_access)
):
    data = []
    vaccination_sites = await VaccinacionSite.find_all().to_list()
    for date in calendar.Calendar().itermonthdates(year, month):
        if date.month != month:
            continue
        for vaccination_site in vaccination_sites:
            data.append(
                Calendar(
                    date=date,
                    vaccination_site=vaccination_site.id,
                    is_available=True,
                    total_schedules=schedules,
                    remaining_schedules=schedules,
                )
            )
    await Calendar.insert_many(data)


@admin_router.post("/vaccination-sites/seed")
async def seed_vaccination_sites(_: bool = Depends(check_admin_access)):
    count = 50
    data = []
    for _ in range(count):
        person = mimesis.Person()
        address = mimesis.Address(locale='pt-br')

        neighborhoods = ['Centro', 'Cristo Redentor', 'Mangabeira']

        data.append(
            VaccinacionSite(
                name=person.full_name(),
                address=Address(
                    street_name=address.street_name(),
                    street_number=address.street_number(),
                    neighborhood=random.choice(neighborhoods),
                ),
                geo=GeoJson2DPoint(coordinates=(address.longitude(), address.latitude())),
            )
        )
    await VaccinacionSite.insert_many(data)
