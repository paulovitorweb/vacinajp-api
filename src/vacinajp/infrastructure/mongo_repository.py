import datetime
from contextlib import asynccontextmanager
from typing import AsyncIterator
from typing import List, Optional

from pymongo.errors import DuplicateKeyError
from pymongo.client_session import ClientSession
from beanie import PydanticObjectId

from src.vacinajp.common.errors import UserAlreadyExists
from src.vacinajp.domain.models import (
    Schedule,
    Calendar,
    UserInfo,
    User,
    VaccinacionSite,
    Vaccine,
    AdminCalendar,
)


class MongoUnitOfWork:

    _session: ClientSession

    def __init__(self, session: ClientSession):
        self._session = session

    @asynccontextmanager
    async def __call__(self, transactional: bool = False) -> AsyncIterator['MongoUnitOfWork']:
        if transactional:
            async with self._session.start_transaction():
                yield self
        else:
            yield self

    @property
    def schedules(self) -> 'MongoScheduleRepository':
        return MongoScheduleRepository(session=self._session)

    @property
    def users(self) -> 'MongoUserRepository':
        return MongoUserRepository(session=self._session)

    @property
    def calendar(self) -> 'MongoCalendarRepository':
        return MongoCalendarRepository(session=self._session)

    @property
    def vaccination_sites(self) -> 'MongoVaccinationSiteRepository':
        return MongoVaccinationSiteRepository(session=self._session)

    @property
    def vaccines(self) -> 'MongoVaccineRepository':
        return MongoVaccineRepository(session=self._session)


class MongoScheduleRepository:

    _session: ClientSession

    def __init__(self, session: ClientSession):
        self._session = session

    async def create(self, schedule: Schedule) -> Schedule:
        return await schedule.insert(session=self._session)

    async def get(
        self, user_id: PydanticObjectId, date: datetime.date, vaccination_site_id: PydanticObjectId
    ) -> Schedule:
        return await Schedule.find_one(
            Schedule.user == user_id,
            Schedule.date == date,
            Schedule.vaccination_site == vaccination_site_id,
        )

    async def update(self, schedule: Schedule) -> None:
        await schedule.replace(session=self._session)


class MongoVaccinationSiteRepository:

    _session: ClientSession

    def __init__(self, session: ClientSession):
        self._session = session

    async def get(self, vaccination_site_id: PydanticObjectId) -> VaccinacionSite:
        return await VaccinacionSite.get(vaccination_site_id)


class MongoVaccineRepository:

    _session: ClientSession

    def __init__(self, session: ClientSession):
        self._session = session

    async def create(self, vaccine: Vaccine) -> Vaccine:
        return await vaccine.insert(session=self._session)


class MongoCalendarRepository:

    _session: ClientSession

    def __init__(self, session: ClientSession):
        self._session = session

    async def get_available_calendar_from_schedule(self, schedule: Schedule) -> Calendar:
        filters = [
            Calendar.date == schedule.date,
            Calendar.vaccination_site == schedule.vaccination_site,
            Calendar.remaining_schedules > 0,
            Calendar.is_available == True,  # noqa
        ]
        return await Calendar.find_one(*filters)

    async def get_available_sites_to_schedule_from_date(
        self, date: datetime.date
    ) -> List[VaccinacionSite]:
        filters = [
            Calendar.date == date,
            Calendar.remaining_schedules > 0,
            Calendar.is_available == True,  # noqa
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

    async def get(self, date: datetime.date, vaccination_site_id: PydanticObjectId) -> Calendar:
        filters = [Calendar.date == date, Calendar.vaccination_site == vaccination_site_id]
        return await Calendar.find_one(*filters)

    async def change_available_schedules_from_calendar(
        self,
        date: datetime.date,
        vaccination_site_id: PydanticObjectId,
        is_available: Optional[bool] = None,
        schedules_variation: Optional[int] = None,
    ) -> None:
        """
        Change available schedules from specific calendar, identified by date and vaccination site.
            Only updates if the resulting amount of remaining schedules is greater than or equal to 0.

        :param date: datetime.date
        :param vaccination_site_id: PydanticObjectId
        :param is_available: Optional[bool] - whether the vaccination site should be available
        :param schedules_variation: Optional[int] - the variation of available schedules
        :return: None
        """
        filters = [Calendar.date == date, Calendar.vaccination_site == vaccination_site_id]
        update = {}

        if isinstance(schedules_variation, int):
            update["$inc"] = {
                Calendar.remaining_schedules: schedules_variation,
                Calendar.total_schedules: schedules_variation,
            }
            if schedules_variation < 0:
                filters.append(Calendar.remaining_schedules >= -schedules_variation)

        if isinstance(is_available, bool):
            update["$set"] = {Calendar.is_available: is_available}

        assert not update, "No modifications to perform"

        query_result = await Calendar.find_one(*filters).update(update, session=self._session)

        assert query_result.modified_count == 1, "No modifications have been made"

    async def decrease_remaining_schedules(self, calendar: Calendar) -> None:
        await calendar.update({"$inc": {Calendar.remaining_schedules: -1}}, session=self._session)

    async def increase_vaccines_applied(self, calendar: Calendar) -> None:
        await calendar.update({"$inc": {Calendar.applied_vaccines: 1}}, session=self._session)

    async def update_calendar(self, calendar: Calendar) -> None:
        await calendar.replace(session=self._session)

    async def get_calendar_with_vaccination_site_from_date(
        self, date: datetime.date
    ) -> List[AdminCalendar]:
        available_sites = (
            await Calendar.find(Calendar.date == date)
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
                ],
                projection_model=AdminCalendar,
            )
            .to_list()
        )
        return available_sites


class MongoUserRepository:

    _session: ClientSession

    def __init__(self, session: Optional[ClientSession] = None):
        self._session = session

    async def update(self, user: User) -> None:
        await user.replace(session=self._session)

    async def get(self, user_id: PydanticObjectId) -> User:
        return await User.get(user_id, session=self._session)

    async def get_from_cpf(self, cpf: str) -> User:
        return await User.find_one(User.cpf == cpf, session=self._session)

    async def get_user_info(self, user_id: PydanticObjectId) -> UserInfo:
        user = (
            await User.find(User.id == user_id, session=self._session)
            .aggregate(
                [
                    {
                        "$lookup": {
                            "from": "vaccines",
                            "localField": "_id",
                            "foreignField": "user",
                            "as": "vaccine_card",
                        }
                    },
                    {
                        "$lookup": {
                            "from": "schedules",
                            "localField": "_id",
                            "foreignField": "user",
                            "as": "schedules",
                        }
                    },
                ],
                session=self._session,
                projection_model=UserInfo,
            )
            .to_list()
        )

        if user:
            return user[0]

    async def create(self, user: User) -> User:
        try:
            return await user.insert(session=self._session)
        except DuplicateKeyError:
            raise UserAlreadyExists("User with provided cpf already exists")
