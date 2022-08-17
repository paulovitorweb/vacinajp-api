import datetime

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from src.vacinajp.domain.models import Schedule, UserInfo
from src.vacinajp.infrastructure.mongo_client import client
from src.vacinajp.api.dependencies import get_current_user


schedule_router = APIRouter()


class ScheduleCreate(BaseModel):
    date: datetime.date
    vaccination_site: str


@schedule_router.post("/", response_model=Schedule)
async def create_schedule(
    schedule: ScheduleCreate, current_user: UserInfo = Depends(get_current_user)
):
    async with client.start_transaction() as repo:
        schedule = Schedule(user=current_user.id, **schedule.dict())
        calendar = await repo.get_available_calendar_from_schedule(schedule)
        if not calendar:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Schedule not available for this date and vaccination site",
            )
        site = await repo.get_vaccination_site(calendar.vaccination_site)
        schedule.vaccination_site_name = site.name
        schedule = await repo.create_schedule(schedule)
        await repo.decrease_remaining_schedules(calendar)
        return schedule
