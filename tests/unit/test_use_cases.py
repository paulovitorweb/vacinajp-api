from unittest.mock import AsyncMock
from datetime import datetime

import pytest
from pytest_mock import MockerFixture
from beanie import PydanticObjectId
from bson import ObjectId

from src.vacinajp.domain.models import Vaccine, VaccineLaboratory, Calendar, Schedule
from src.vacinajp.domain.use_cases import CreateVaccineUseCase


pytestmark = pytest.mark.asyncio


async def test__create_vaccine_use_case_should_create_vaccine(mocker: MockerFixture):
    uow_mock = AsyncMock()
    vaccine = get_vaccine()

    use_case = CreateVaccineUseCase(uow=uow_mock, vaccine=vaccine)
    await use_case.exec()

    create_vaccine_method: AsyncMock = uow_mock.vaccines.create

    create_vaccine_method.assert_awaited_once_with(vaccine)


async def test__create_vaccine_use_case_should_increase_vaccines_applied(mocker: MockerFixture):
    uow_mock = AsyncMock()
    vaccine = get_vaccine()
    calendar = get_calendar()

    get_calendar_method: AsyncMock = uow_mock.calendar.get
    get_calendar_method.return_value = calendar

    use_case = CreateVaccineUseCase(uow=uow_mock, vaccine=vaccine)
    await use_case.exec()

    get_calendar_kwargs = get_calendar_method.call_args[1]
    assert get_calendar_kwargs == {
        'date': calendar.date,
        'vaccination_site_id': calendar.vaccination_site,
    }

    increase_vaccines_applied_method: AsyncMock = uow_mock.calendar.increase_vaccines_applied
    increase_vaccines_applied_method.assert_awaited_once_with(calendar)


async def test__create_vaccine_use_case_should_not_update_schedule(mocker: MockerFixture):
    uow_mock = AsyncMock()
    vaccine = get_vaccine()

    get_schedule_method: AsyncMock = uow_mock.schedules.get
    get_schedule_method.return_value = None
    update_schedule_method: AsyncMock = uow_mock.schedules.update

    use_case = CreateVaccineUseCase(uow=uow_mock, vaccine=vaccine)
    await use_case.exec()

    get_schedule_kwargs = get_schedule_method.call_args[1]
    assert get_schedule_kwargs == {
        'user_id': vaccine.user,
        'date': vaccine.date,
        'vaccination_site_id': vaccine.vaccination_site,
    }

    update_schedule_method.assert_not_awaited()


async def test__create_vaccine_use_case_should_update_schedule(mocker: MockerFixture):
    uow_mock = AsyncMock()
    vaccine = get_vaccine()
    schedule = get_schedule()

    async def add_id_to_vaccine(vaccine: Vaccine) -> Vaccine:
        vaccine.id = PydanticObjectId('630a44640706d38696810987')
        return vaccine

    create_vaccine_method: AsyncMock = uow_mock.vaccines.create
    create_vaccine_method.side_effect = add_id_to_vaccine
    get_schedule_method: AsyncMock = uow_mock.schedules.get
    get_schedule_method.return_value = schedule
    update_schedule_method: AsyncMock = uow_mock.schedules.update

    use_case = CreateVaccineUseCase(uow=uow_mock, vaccine=vaccine)
    await use_case.exec()

    get_schedule_kwargs = get_schedule_method.call_args[1]
    assert get_schedule_kwargs == {
        'user_id': vaccine.user,
        'date': vaccine.date,
        'vaccination_site_id': vaccine.vaccination_site,
    }

    updated_schedule: Schedule = update_schedule_method.call_args[0][0]

    assert updated_schedule.user_attended is True
    assert updated_schedule.vaccine == ObjectId('630a44640706d38696810987')


def get_vaccine() -> Vaccine:
    return Vaccine(
        user=PydanticObjectId('630a44640706d38696819294'),
        date=datetime(2022, 8, 10).date(),
        vaccination_site=PydanticObjectId('630a44640706d38696811103'),
        vaccination_site_name='Test',
        dose=1,
        laboratory=VaccineLaboratory.JANSSEN,
        professional=PydanticObjectId('630a44640706d38696822290'),
    )


def get_calendar() -> Calendar:
    return Calendar(
        id=PydanticObjectId('630a44640706d38696885199'),
        date=datetime(2022, 8, 10).date(),
        vaccination_site=PydanticObjectId('630a44640706d38696811103'),
        total_schedules=100,
        remaining_schedules=100,
        is_available=True,
    )


def get_schedule() -> Schedule:
    return Schedule(
        user=PydanticObjectId('630a44640706d38696819294'),
        date=datetime(2022, 8, 10).date(),
        vaccination_site=PydanticObjectId('630a44640706d38696811103'),
        vaccination_site_name='Test',
    )
