import datetime

from pydantic import BaseModel
from fastapi import APIRouter, Response, status
from src.vacinajp.domain.models import Schedule
from src.vacinajp.infrastructure.mongo_client import client


schedule_router = APIRouter()


class ScheduleCreate(BaseModel):
    user: str
    date : datetime.date
    vaccination_site : str


@schedule_router.post("/")
async def create_schedule(schedule: ScheduleCreate):
    await create_schedule_view(schedule)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def create_schedule_view(schedule: ScheduleCreate):
    async with client.start_transaction() as repo:
        schedule = Schedule(**schedule.dict())
        calendar = await repo.get_available_calendar_from_schedule(schedule)
        if not calendar:
            raise ValueError("Local não disponível para esta data")
        site = await repo.get_vaccination_site(calendar.vaccination_site)
        schedule.vaccination_site_name = site.name
        await repo.create_schedule(schedule)
        await repo.decrease_remaining_schedules(calendar)
