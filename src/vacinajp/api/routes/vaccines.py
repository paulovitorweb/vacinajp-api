import datetime

from pydantic import BaseModel
from fastapi import APIRouter
from src.vacinajp.domain.models import Vaccine
from src.vacinajp.infrastructure.mongo_client import client


vaccine_router = APIRouter()


class VaccineCreate(BaseModel):
    user: str
    date: datetime.date
    vaccination_site: str
    dose: int
    laboratory: str = "Pfizer"


@vaccine_router.post("/")
async def create_vaccine(vaccine: VaccineCreate):
    async with client.start_transaction() as repo:
        vaccine = Vaccine(**vaccine.dict())
        site = await repo.get_vaccination_site(vaccine.vaccination_site)

        vaccine.vaccination_site_name = site.name
        created_vaccine = await repo.create_vaccine(vaccine)

        calendar = await repo.get_calendar(
            date=vaccine.date,
            vaccination_site=vaccine.vaccination_site
        )
        await repo.increase_vaccines_applied(calendar)

        schedule = await repo.get_schedule(
            user_id=vaccine.user,
            date=vaccine.date,
            vaccination_site_id=vaccine.vaccination_site
        )
        if schedule:
            schedule.user_attended = True
            schedule.vaccine = created_vaccine.id
            await repo.update_schedule(schedule)
