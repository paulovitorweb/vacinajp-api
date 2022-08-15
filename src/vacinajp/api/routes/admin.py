import datetime
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel
from beanie import PydanticObjectId

from src.vacinajp.domain.models import AdminCalendar, UserRole
from src.vacinajp.infrastructure.mongo_client import client
from src.vacinajp.common.helpers import SecurityHelper


admin_router = APIRouter()


class CalendarUpdate(BaseModel):
    is_available: bool


class RoleToUser(BaseModel):
    roles: List[UserRole]


class PasswordToUser(BaseModel):
    password: str


@admin_router.patch("/calendar/{year}/{month}/{day}/{vaccination_site_id}")
async def update_calendar(
    year: int,
    month: int,
    day: int,
    vaccination_site_id: PydanticObjectId,
    calendar_update: CalendarUpdate,
):
    async with client.start_transaction() as repo:
        calendar = await repo.get_calendar(
            date=datetime.date(year=year, month=month, day=day),
            vaccination_site_id=vaccination_site_id,
        )
        calendar.is_available = calendar_update.is_available
        await repo.update_calendar(calendar)


@admin_router.get("/stats/{year}/{month}/{day}/", response_model=List[AdminCalendar])
async def get_stats_from_date(year: int, month: int, day: int):
    async with client.start_transaction() as repo:
        return await repo.get_calendar_with_vaccination_site_from_date(
            date=datetime.date(year=year, month=month, day=day)
        )


@admin_router.patch("/users/{user_id}/roles")
async def set_role_to_user(user_id: PydanticObjectId, role_to_user: RoleToUser):
    async with client.start_transaction() as repo:
        await repo.set_user_role(user_id=user_id, user_roles=role_to_user.roles)


@admin_router.patch("/users/{user_id}/generate-password", response_model=PasswordToUser)
async def generate_password(user_id: PydanticObjectId):
    async with client.start_transaction() as repo:
        user = await repo.get_user(user_id=user_id)
        password = SecurityHelper.generate_safe_password()
        hashed_password = SecurityHelper.get_password_hash(password)
        user.hashed_password = hashed_password
        await repo.update_user(user)
        return {'password': password}
