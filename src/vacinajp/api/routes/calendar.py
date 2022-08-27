import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from beanie import PydanticObjectId

from src.vacinajp.domain.models import UserInfo, AdminCalendar, VaccinacionSite
from src.vacinajp.infrastructure.mongo_repository import MongoUnitOfWork
from src.vacinajp.api.dependencies import get_current_user, get_current_operator_user, get_uow


calendar_router = APIRouter()


class CalendarUpdate(BaseModel):
    is_available: Optional[bool] = None
    available_schedules_variation: Optional[int] = None


@calendar_router.get("/{year}/{month}/{day}", response_model=List[VaccinacionSite])
async def get_available_sites_to_schedule_from_date(
    year: int,
    month: int,
    day: int,
    current_user: UserInfo = Depends(get_current_user),
    uow: MongoUnitOfWork = Depends(get_uow),
):
    async with uow():
        return await uow.calendar.get_available_sites_to_schedule_from_date(
            datetime.date(year=year, month=month, day=day)
        )


@calendar_router.patch("/{year}/{month}/{day}/{vaccination_site_id}")
async def update_calendar(
    year: int,
    month: int,
    day: int,
    vaccination_site_id: PydanticObjectId,
    calendar_update: CalendarUpdate,
    current_user: UserInfo = Depends(get_current_operator_user),
    uow: MongoUnitOfWork = Depends(get_uow),
):
    if (
        calendar_update.is_available is None
        and calendar_update.available_schedules_variation is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide something to be updated",
        )
    async with uow:
        try:
            await uow.calendar.change_available_schedules_from_calendar(
                date=datetime.date(year=year, month=month, day=day),
                vaccination_site_id=vaccination_site_id,
                is_available=calendar_update.is_available,
                schedules_variation=calendar_update.available_schedules_variation,
            )
        except AssertionError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The calendar could not be updated. Check the number of schedules available.",
            )


@calendar_router.get("/stats/{year}/{month}/{day}/", response_model=List[AdminCalendar])
async def get_stats_from_date(
    year: int,
    month: int,
    day: int,
    current_user: UserInfo = Depends(get_current_operator_user),
    uow: MongoUnitOfWork = Depends(get_uow),
):
    async with uow():
        return await uow.calendar.get_calendar_with_vaccination_site_from_date(
            date=datetime.date(year=year, month=month, day=day)
        )
