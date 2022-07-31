import datetime
from pymongo.client_session import ClientSession
from beanie import PydanticObjectId
from .repository import Repository
from ..domain.models import Schedule, Calendar, UserInfo, User, VaccinacionSite, Vaccine


class MongoRepository(Repository):

    _session: ClientSession

    def __init__(self, session: ClientSession):
        self._session = session

    async def create_schedule(self, schedule: Schedule) -> None:
        await schedule.insert(session=self._session)

    async def get_available_calendar_from_schedule(self, schedule: Schedule) -> Calendar:
        filters = [
            Calendar.date == schedule.date,
            Calendar.vaccination_site == schedule.vaccination_site,
            Calendar.remaining_schedules > 0,
            Calendar.is_available == True
        ]
        return await Calendar.find_one(*filters)
    
    async def decrease_remaining_schedules(self, calendar: Calendar) -> None:
        await calendar.update({"$inc": {Calendar.remaining_schedules: -1}}, session=self._session)

    async def get_schedule(self, user_id: PydanticObjectId, date: datetime.date, vaccination_site_id: PydanticObjectId) -> Schedule:
        return await Schedule.find_one(
            Schedule.user == user_id,
            Schedule.date == date,
            Schedule.vaccination_site == vaccination_site_id
        )
    
    async def update_schedule(self, schedule: Schedule) -> None:
        await schedule.replace(session=self._session)
    
    async def get_user(self, user_id: PydanticObjectId) -> UserInfo:
        user = await User.find(User.id == user_id).aggregate([
            {"$lookup": {
                "from": "vaccines",
                "localField": "_id",
                "foreignField": "user",
                "as": "vaccine_card"
            }},
            {"$lookup": {
                "from": "schedules",
                "localField": "_id",
                "foreignField": "user",
                "as": "schedules"
            }}
        ], projection_model=UserInfo).to_list()

        if user:
            return user[0]

    async def create_user(self, user: User) -> None:
        await user.insert(session=self._session)
    
    async def get_vaccination_site(self, vaccination_site_id: PydanticObjectId) -> VaccinacionSite:
        return await VaccinacionSite.get(vaccination_site_id)

    async def create_vaccine(self, vaccine: Vaccine) -> Vaccine:
        return await vaccine.insert(session=self._session)
