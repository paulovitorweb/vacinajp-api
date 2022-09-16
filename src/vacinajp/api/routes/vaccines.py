import datetime

from pydantic import BaseModel
from fastapi import APIRouter, Depends

from src.vacinajp.domain.models import Vaccine, VaccineLaboratory, UserInfo
from src.vacinajp.domain.use_cases import CreateVaccineUseCase
from src.vacinajp.infrastructure.repository import UnitOfWork
from src.vacinajp.api.dependencies import get_current_professional_user, get_uow


vaccine_router = APIRouter()


class VaccineCreate(BaseModel):
    user: str
    date: datetime.date
    vaccination_site: str
    dose: int
    laboratory: VaccineLaboratory


@vaccine_router.post("/", status_code=201, response_model=Vaccine)
async def create_vaccine(
    vaccine: VaccineCreate,
    current_user: UserInfo = Depends(get_current_professional_user),
    uow: UnitOfWork = Depends(get_uow),
):
    async with uow(transactional=True):
        site = await uow.vaccination_sites.get(vaccine.vaccination_site)

        vaccine = Vaccine(
            **vaccine.dict(), vaccination_site_name=site.name, professional=current_user.id
        )

        use_case = CreateVaccineUseCase(uow=uow, vaccine=vaccine)
        await use_case.exec()

        return use_case.created_vaccine
