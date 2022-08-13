import datetime
import pytest

from httpx import AsyncClient
from beanie import PydanticObjectId, operators

from src.vacinajp.domain.models import (
    User,
    UserRole,
    Schedule,
    Calendar,
    Vaccine,
    VaccineLaboratory,
)


pytestmark = pytest.mark.asyncio


class TestContext:
    user_id: str
    vaccination_site_id: str


test_context = TestContext()


async def test__create_user(test_app: AsyncClient):
    payload = {'name': 'Son Goku'}
    response = await test_app.post('/users/', json=payload)
    assert response.status_code == 200

    json = response.json()
    assert json['name'] == 'Son Goku'
    assert json['roles'] == []
    assert json['_id'] is not None

    test_context.user_id = json['_id']


async def test__admin_set_role_to_user(test_app: AsyncClient):
    payload = {'roles': ['HEALTHCARE_PROFESSIONAL']}
    response = await test_app.patch(f'/admin/users/{test_context.user_id}/roles', json=payload)
    assert response.status_code == 200
    user = await User.get(PydanticObjectId(test_context.user_id))
    assert user.roles == [UserRole.HEALTHCARE_PROFESSIONAL]


async def test__get_user(test_app: AsyncClient):
    response = await test_app.get(f'/users/{test_context.user_id}')
    assert response.status_code == 200
    json = response.json()
    assert json['name'] == 'Son Goku'
    assert json['roles'] == ['HEALTHCARE_PROFESSIONAL']
    assert json['_id'] is not None


async def test__admin_unset_role_to_user(test_app: AsyncClient):
    payload = {'roles': []}
    response = await test_app.patch(f'/admin/users/{test_context.user_id}/roles', json=payload)
    assert response.status_code == 200
    user = await User.get(PydanticObjectId(test_context.user_id))
    assert user.roles == []


async def test__get_available_sites_to_schedule_from_date(test_app: AsyncClient):
    response = await test_app.get(f'/calendar/2022/8/2/vaccination-sites')
    assert response.status_code == 200
    json = response.json()
    assert len(json) > 0
    sites_available_before = len(json)
    test_context.vaccination_site_ids = [json[0]['_id'], json[1]['_id'], json[3]['_id']]

    sites_to_make_unavailable = await Calendar.find(
        operators.In(
            Calendar.vaccination_site,
            [PydanticObjectId(site_id) for site_id in test_context.vaccination_site_ids[:2]],
        ),
        Calendar.date == datetime.date(year=2022, month=8, day=2),
    ).to_list()
    sites_to_make_unavailable[0].is_available = False
    await sites_to_make_unavailable[0].replace()
    sites_to_make_unavailable[1].remaining_schedules = 0
    await sites_to_make_unavailable[1].replace()

    response = await test_app.get(f'/calendar/2022/8/2/vaccination-sites')
    assert response.status_code == 200
    assert len(response.json()) == sites_available_before - 2


async def test__create_schedule(test_app: AsyncClient):
    calendar_before = await get_calendar()
    payload = {
        'user': test_context.user_id,
        'date': '2022-08-12',
        'vaccination_site': test_context.vaccination_site_ids[2],
    }
    response = await test_app.post('/schedules/', json=payload)
    assert response.status_code == 204

    schedule = await Schedule.find_one(Schedule.user == PydanticObjectId(test_context.user_id))
    assert schedule.date == datetime.date(year=2022, month=8, day=12)
    assert schedule.vaccination_site == PydanticObjectId(test_context.vaccination_site_ids[2])
    assert schedule.vaccination_site_name
    assert schedule.user_attended is False
    assert schedule.vaccine is None

    calendar_after = await get_calendar()
    assert calendar_after.remaining_schedules == calendar_before.remaining_schedules - 1


async def test__create_vaccine(test_app: AsyncClient):
    calendar_before = await get_calendar()
    payload = {
        'user': test_context.user_id,
        'date': '2022-08-12',
        'vaccination_site': test_context.vaccination_site_ids[2],
        'dose': 1,
        'laboratory': 'PFIZER',
    }
    response = await test_app.post('/vaccines/', json=payload)
    assert response.status_code == 200

    vaccine = await Vaccine.find_one(Vaccine.user == PydanticObjectId(test_context.user_id))
    assert vaccine.date == datetime.date(year=2022, month=8, day=12)
    assert vaccine.vaccination_site == PydanticObjectId(test_context.vaccination_site_ids[2])
    assert vaccine.vaccination_site_name
    assert vaccine.dose == 1
    assert vaccine.laboratory == VaccineLaboratory.PFIZER

    calendar_after = await get_calendar()
    assert calendar_after.applied_vaccines == calendar_before.applied_vaccines + 1

    schedule = await Schedule.find_one(
        Schedule.date == datetime.date(year=2022, month=8, day=12),
        Schedule.vaccination_site == PydanticObjectId(test_context.vaccination_site_ids[2]),
        Schedule.user == PydanticObjectId(test_context.user_id),
    )
    assert schedule.user_attended is True
    assert schedule.vaccine == vaccine.id


async def test__admin_get_stats(test_app: AsyncClient):
    response = await test_app.get('/admin/stats/2022/8/2/')
    assert response.status_code == 200
    assert len(response.json()) > 0

    first_item = response.json()[0]
    assert first_item['_id'] is not None
    assert first_item['date'] is not None
    assert first_item['vaccination_site'] is not None
    assert first_item['total_schedules'] is not None
    assert first_item['remaining_schedules'] is not None
    assert first_item['is_available'] is not None
    assert first_item['applied_vaccines'] is not None
    assert first_item['vaccination_site_info'] is not None


async def get_calendar() -> Calendar:
    return await Calendar.find_one(
        Calendar.date == datetime.date(year=2022, month=8, day=12),
        Calendar.vaccination_site == PydanticObjectId(test_context.vaccination_site_ids[2]),
    )
