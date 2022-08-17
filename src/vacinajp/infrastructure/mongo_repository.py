import datetime
from typing import List, Optional
from pymongo.client_session import ClientSession
from beanie import PydanticObjectId
from beanie.odm.queries.find import FindOne
from .repository import Repository
from ..domain.models import (
    Schedule,
    Calendar,
    UserInfo,
    User,
    VaccinacionSite,
    Vaccine,
    AdminCalendar,
    UserRole,
)


class MongoRepository(Repository):

    _session: ClientSession

    def __init__(self, session: ClientSession):
        self._session = session

    async def create_schedule(self, schedule: Schedule) -> Schedule:
        return await schedule.insert(session=self._session)

    async def get_available_calendar_from_schedule(self, schedule: Schedule) -> Calendar:
        filters = [
            Calendar.date == schedule.date,
            Calendar.vaccination_site == schedule.vaccination_site,
            Calendar.remaining_schedules > 0,
            Calendar.is_available == True,
        ]
        return await Calendar.find_one(*filters)

    async def get_calendar(
        self, date: datetime.date, vaccination_site_id: PydanticObjectId
    ) -> Calendar:
        filters = [Calendar.date == date, Calendar.vaccination_site == vaccination_site_id]
        return await Calendar.find_one(*filters)

    async def change_available_schedules_from_calendar(
        self,
        date: datetime.date,
        vaccination_site_id: PydanticObjectId,
        is_available: Optional[bool] = None,
        schedules_variation: Optional[int] = None,
    ) -> bool:
        """
        Change available schedules from specific calendar, identified by date and vaccination site.
            Only updates if the resulting amount of remaining schedules is greater than or equal to 0.

        :param date: datetime.date
        :param vaccination_site_id: PydanticObjectId
        :param is_available: Optional[bool] - whether the vaccination site should be available
        :param schedules_variation: Optional[int] - the variation of available schedules
        :return: bool - True if updated, false otherwise
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

        if not update:
            return False

        query_result = await Calendar.find_one(*filters).update(update, session=self._session)

        if query_result.modified_count == 1:
            return True

        return False

    async def decrease_remaining_schedules(self, calendar: Calendar) -> None:
        await calendar.update({"$inc": {Calendar.remaining_schedules: -1}}, session=self._session)

    async def increase_vaccines_applied(self, calendar: Calendar) -> None:
        await calendar.update({"$inc": {Calendar.applied_vaccines: 1}}, session=self._session)

    async def update_calendar(self, calendar: Calendar) -> None:
        await calendar.replace(session=self._session)

    async def get_schedule(
        self, user_id: PydanticObjectId, date: datetime.date, vaccination_site_id: PydanticObjectId
    ) -> Schedule:
        return await Schedule.find_one(
            Schedule.user == user_id,
            Schedule.date == date,
            Schedule.vaccination_site == vaccination_site_id,
        )

    async def update_schedule(self, schedule: Schedule) -> None:
        await schedule.replace(session=self._session)

    async def get_user(self, user_id: PydanticObjectId) -> User:
        return await User.get(user_id)

    async def update_user(self, user: User) -> None:
        await user.replace(session=self._session)

    async def get_user_from_cpf(self, cpf: str) -> User:
        return await User.find_one(User.cpf == cpf)

    async def get_user_info(self, user_id: PydanticObjectId) -> UserInfo:
        user = (
            await User.find(User.id == user_id)
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
                projection_model=UserInfo,
            )
            .to_list()
        )

        if user:
            return user[0]

    async def create_user(self, user: User) -> User:
        return await user.insert(session=self._session)

    async def set_user_role(self, user_id: PydanticObjectId, user_roles: List[UserRole]) -> None:
        await User.find_one(User.id == user_id).update({'$set': {User.roles: user_roles}})

    async def get_vaccination_site(self, vaccination_site_id: PydanticObjectId) -> VaccinacionSite:
        return await VaccinacionSite.get(vaccination_site_id)

    async def create_vaccine(self, vaccine: Vaccine) -> Vaccine:
        return await vaccine.insert(session=self._session)

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

    async def get_vaccines_from(self, date: datetime.date) -> List[AdminCalendar]:
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
