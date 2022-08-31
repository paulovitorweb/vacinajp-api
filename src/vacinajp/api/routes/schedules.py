import datetime

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status

from src.vacinajp.common.errors import ScheduleNotAvailable
from src.vacinajp.domain.models import Schedule, UserInfo
from src.vacinajp.domain.use_cases import CreateScheduleUseCase
from src.vacinajp.infrastructure.mongo_repository import MongoUnitOfWork
from src.vacinajp.api.dependencies import get_current_user, get_uow


schedule_router = APIRouter()


class ScheduleCreate(BaseModel):
    date: datetime.date
    vaccination_site: str


@schedule_router.post("/", response_model=Schedule, status_code=201)
async def create_schedule(
    schedule: ScheduleCreate,
    current_user: UserInfo = Depends(get_current_user),
    uow: MongoUnitOfWork = Depends(get_uow),
):
    async with uow(transactional=True):
        schedule = Schedule(user=current_user.id, **schedule.dict())
        use_case = CreateScheduleUseCase(uow=uow, schedule=schedule)
        try:
            await use_case.exec()
        except ScheduleNotAvailable as err:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err)

        return use_case.created_schedule
