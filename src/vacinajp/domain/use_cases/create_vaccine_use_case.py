from typing import Optional

from src.vacinajp.domain.models import Vaccine
from src.vacinajp.infrastructure.repository import UnitOfWork


class CreateVaccineUseCase:
    def __init__(self, uow: UnitOfWork, vaccine: Vaccine) -> None:
        self._uow: UnitOfWork = uow
        self._vaccine: Vaccine = vaccine

        self._created_vaccine: Optional[Vaccine] = None

    async def exec(self) -> None:
        self._created_vaccine = await self._uow.vaccines.create(self._vaccine)

        calendar = await self._uow.calendar.get(
            date=self._vaccine.date, vaccination_site_id=self._vaccine.vaccination_site
        )

        await self._uow.calendar.increase_vaccines_applied(calendar)

        schedule = await self._uow.schedules.get(
            user_id=self._vaccine.user,
            date=self._vaccine.date,
            vaccination_site_id=self._vaccine.vaccination_site,
        )

        if schedule:
            schedule.user_attended = True
            schedule.vaccine = self._created_vaccine.id
            await self._uow.schedules.update(schedule)

    @property
    def created_vaccine(self) -> Optional[Vaccine]:
        return self._created_vaccine
