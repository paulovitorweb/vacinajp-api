import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from beanie import PydanticObjectId
from src.vacinajp.domain.models import VaccinacionSite, Calendar, UserInfo, AdminCalendar
from src.vacinajp.infrastructure.mongo_client import client
from src.vacinajp.api.dependencies import get_current_user, get_current_operator_user


calendar_router = APIRouter()


class CalendarUpdate(BaseModel):
    is_available: Optional[bool] = None
    available_schedules_variation: Optional[int] = None


@calendar_router.get("/{year}/{month}/{day}")
async def get_available_sites_to_schedule_from_date(
    year: int,
    month: int,
    day: int,
    current_user: UserInfo = Depends(get_current_user),
):
    filters = [
        Calendar.date == datetime.date(year=year, month=month, day=day),
        Calendar.remaining_schedules > 0,
        Calendar.is_available == True,
    ]
    available_sites = (
        await Calendar.find(*filters)
        .aggregate(
            [
                {
                    "$lookup": {
                        "from": "vaccination_sites",
                        "localField": "vaccination_site",
                        "foreignField": "_id",
                        "as": "vaccination_site_info",
                    }
                },
                {"$unwind": "$vaccination_site_info"},
                {
                    "$project": {
                        "_id": "$vaccination_site_info._id",
                        "name": "$vaccination_site_info.name",
                        "address": "$vaccination_site_info.address",
                        "geo": "$vaccination_site_info.geo",
                    }
                },
            ],
            projection_model=VaccinacionSite,
        )
        .to_list()
    )
    return available_sites


@calendar_router.patch("/{year}/{month}/{day}/{vaccination_site_id}")
async def update_calendar(
    year: int,
    month: int,
    day: int,
    vaccination_site_id: PydanticObjectId,
    calendar_update: CalendarUpdate,
    current_user: UserInfo = Depends(get_current_operator_user),
):
    if (
        calendar_update.is_available is None
        and calendar_update.available_schedules_variation is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide something to be updated",
        )
    async with client.start_transaction() as repo:
        if not await repo.change_available_schedules_from_calendar(
            date=datetime.date(year=year, month=month, day=day),
            vaccination_site_id=vaccination_site_id,
            is_available=calendar_update.is_available,
            schedules_variation=calendar_update.available_schedules_variation,
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The calendar could not be updated. Check the number of schedules available.",
            )


@calendar_router.get("/stats/{year}/{month}/{day}/", response_model=List[AdminCalendar])
async def get_stats_from_date(
    year: int, month: int, day: int, current_user: UserInfo = Depends(get_current_operator_user)
):
    async with client.start_transaction() as repo:
        return await repo.get_calendar_with_vaccination_site_from_date(
            date=datetime.date(year=year, month=month, day=day)
        )
