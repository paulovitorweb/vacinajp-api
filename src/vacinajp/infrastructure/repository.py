import abc
import datetime
from typing import List, Union, Optional, AsyncIterator

from bson import ObjectId
from pymongo.client_session import ClientSession

from src.vacinajp.domain.models import (
    Schedule,
    Calendar,
    UserInfo,
    User,
    VaccinacionSite,
    Vaccine,
    AdminCalendar,
)

# New implementations of units of work must ensure that the type alias
# points to the session type and id annotations
Session = Union[ClientSession, None]
Id = Union[ObjectId, int]


class BaseRepository:
    """Base repository with default init for instances"""

    _session: Session

    def __init__(self, session: Session = None):
        self._session = session


class ScheduleRepository(BaseRepository):
    """Schedule repository"""

    @abc.abstractmethod
    async def create(self, schedule: Schedule) -> Schedule:
        """Create and return a schedule"""
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, user_id: Id, date: datetime.date, vaccination_site_id: Id) -> Schedule:
        """Get a schedule"""
        raise NotImplementedError

    @abc.abstractmethod
    async def update(self, schedule: Schedule) -> None:
        """Update a schedule"""
        raise NotImplementedError


class VaccinationSiteRepository(BaseRepository):
    """Vaccination site repository"""

    @abc.abstractmethod
    async def get(self, vaccination_site_id: Id) -> VaccinacionSite:
        """Get a vaccination site"""
        raise NotImplementedError


class VaccineRepository(BaseRepository):
    """Vaccine repository"""

    @abc.abstractmethod
    async def create(self, vaccine: Vaccine) -> Vaccine:
        """Create and return a vaccination site"""
        raise NotImplementedError


class CalendarRepository(BaseRepository):
    """Calendar repository"""

    @abc.abstractmethod
    async def get_available_calendar_from_schedule(self, schedule: Schedule) -> Calendar:
        """Create and return a vaccination site"""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_available_sites_to_schedule_from_date(
        self, date: datetime.date
    ) -> List[VaccinacionSite]:
        """Get available vaccination sites to schedule from date"""
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, date: datetime.date, vaccination_site_id: Id) -> Calendar:
        """Get a calendar"""
        raise NotImplementedError

    @abc.abstractmethod
    async def change_available_schedules_from_calendar(
        self,
        date: datetime.date,
        vaccination_site_id: Id,
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
        raise NotImplementedError

    @abc.abstractmethod
    async def decrease_remaining_schedules(self, calendar: Calendar) -> None:
        """Decrease ramining schedules from calendar by 1"""
        raise NotImplementedError

    @abc.abstractmethod
    async def increase_vaccines_applied(self, calendar: Calendar) -> None:
        """Increase ramining schedules from calendar by 1"""
        raise NotImplementedError

    @abc.abstractmethod
    async def update_calendar(self, calendar: Calendar) -> None:
        """Update a calendar"""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_calendar_with_vaccination_site_from_date(
        self, date: datetime.date
    ) -> List[AdminCalendar]:
        """Get calendar with vaccination sites from date"""
        raise NotImplementedError


class UserRepository(BaseRepository, metaclass=abc.ABCMeta):
    """User repository"""

    @abc.abstractmethod
    async def update(self, user: User) -> None:
        """Update a user"""
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, user_id: Id) -> User:
        """Get a user"""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_from_cpf(self, cpf: str) -> User:
        """Get a user from cpf"""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_user_info(self, user_id: Id) -> UserInfo:
        """Get user info. Includes schedules and vaccine card"""
        raise NotImplementedError

    @abc.abstractmethod
    async def create(self, user: User) -> User:
        """Create and return a user.
        Should raise an UserAlreadyExists exception if a user with the same cpf already exists
        """
        raise NotImplementedError


class BaseUnitOfWork:
    """Base unit of work with default init for instances"""

    _session: Session

    def __init__(self, session: Session):
        self._session = session


class UnitOfWork(BaseUnitOfWork, metaclass=abc.ABCMeta):
    """An interface on which every concrete unit of work must be based"""

    users: UserRepository
    schedules: ScheduleRepository
    calendar: CalendarRepository
    vaccination_sites: VaccinationSiteRepository
    vaccines: VaccineRepository

    @abc.abstractmethod
    async def __call__(self, transactional: bool = False) -> AsyncIterator['UnitOfWork']:
        """An asynchronous context manager for in-transaction and non-transactional operations"""
        raise NotImplementedError
