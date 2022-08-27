import abc


class Repository(abc.ABC):
    @abc.abstractmethod
    async def get_available_calendar_from_schedule(self, schedule):
        raise NotImplementedError

    @abc.abstractmethod
    async def decrease_remaining_schedules(self, calendar) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def create_schedule(self, schedule) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_schedule(self, user_id, date, vaccination_site_id):
        raise NotImplementedError

    @abc.abstractmethod
    async def update_schedule(self, schedule) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_user(self, user_id):
        raise NotImplementedError

    @abc.abstractmethod
    async def create_user(self, user) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_vaccination_site(self, vaccination_site_id):
        raise NotImplementedError

    @abc.abstractmethod
    async def create_vaccine(self, vaccine):
        raise NotImplementedError
