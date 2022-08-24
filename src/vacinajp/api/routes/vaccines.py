import datetime

from pydantic import BaseModel
from fastapi import APIRouter, Depends

from src.vacinajp.domain.models import Vaccine, VaccineLaboratory, UserInfo
from src.vacinajp.infrastructure.mongo_repository import MongoUnitOfWork
from src.vacinajp.api.dependencies import get_current_professional_user, get_uow


vaccine_router = APIRouter()


class VaccineCreate(BaseModel):
    user: str
    date: datetime.date
    vaccination_site: str
    dose: int
    laboratory: VaccineLaboratory


@vaccine_router.post("/", status_code=201)
async def create_vaccine(
    vaccine: VaccineCreate,
    current_user: UserInfo = Depends(get_current_professional_user),
    uow: MongoUnitOfWork = Depends(get_uow),
):
    async with uow(transactional=True):
        site = await uow.vaccination_sites.get(vaccine.vaccination_site)

        vaccine = Vaccine(
            **vaccine.dict(), vaccination_site_name=site.name, professional=current_user.id
        )

        created_vaccine = await uow.vaccines.create(vaccine)

        calendar = await uow.calendar.get(
            date=vaccine.date, vaccination_site_id=vaccine.vaccination_site
        )
        await uow.calendar.increase_vaccines_applied(calendar)

        schedule = await uow.schedules.get(
            user_id=vaccine.user, date=vaccine.date, vaccination_site_id=vaccine.vaccination_site
        )
        if schedule:
            schedule.user_attended = True
            schedule.vaccine = created_vaccine.id
            await uow.schedules.update(schedule)
