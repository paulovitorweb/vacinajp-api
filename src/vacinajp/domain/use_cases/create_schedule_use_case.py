from typing import Optional

from src.vacinajp.common.errors import ScheduleNotAvailable
from src.vacinajp.domain.models import Schedule
from src.vacinajp.infrastructure.mongo_repository import MongoUnitOfWork

# TO DO: implementar interface do UnitOfWork e usar aqui como anotação de tipo
# para o caso de uso ser agnóstico de banco de dados


class CreateScheduleUseCase:
    def __init__(self, uow: MongoUnitOfWork, schedule: Schedule) -> None:
        self._uow: MongoUnitOfWork = uow
        self._schedule: Schedule = schedule

        self._created_schedule: Optional[Schedule] = None

    async def exec(self) -> None:
        calendar = await self._uow.calendar.get_available_calendar_from_schedule(self._schedule)
        if not calendar:
            raise ScheduleNotAvailable("Schedule not available for this date and vaccination site")

        site = await self._uow.vaccination_sites.get(self._schedule.vaccination_site)
        self._schedule.vaccination_site_name = site.name
        self._created_schedule = await self._uow.schedules.create(self._schedule)

        await self._uow.calendar.decrease_remaining_schedules(calendar)

    @property
    def created_schedule(self) -> Optional[Schedule]:
        return self._created_schedule
