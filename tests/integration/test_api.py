import datetime
import pytest
from httpx import AsyncClient
from beanie import PydanticObjectId

from src.vacinajp.domain.models import User, UserRole, Schedule


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


async def test__set_role_to_user(test_app: AsyncClient):
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


async def test__unset_role_to_user(test_app: AsyncClient):
    payload = {'roles': []}
    response = await test_app.patch(f'/admin/users/{test_context.user_id}/roles', json=payload)
    assert response.status_code == 200
    user = await User.get(PydanticObjectId(test_context.user_id))
    assert user.roles == []


async def test__get_available_sites_to_schedule_from_date(test_app: AsyncClient):
    response = await test_app.get(f'/calendar/2022/8/2/vaccination-sites')
    assert response.status_code == 200
    assert len(response.json()) > 0
    test_context.vaccination_site_id = response.json()[0]['_id']


async def test__create_schedule(test_app: AsyncClient):
    payload = {
        'user': test_context.user_id,
        'date': '2022-08-12',
        'vaccination_site': test_context.vaccination_site_id
    }
    response = await test_app.post('/schedules/', json=payload)
    assert response.status_code == 204
    schedule = await Schedule.find_one(Schedule.user == PydanticObjectId(test_context.user_id))
    assert schedule.date == datetime.date(year=2022, month=8, day=12)
    assert schedule.vaccination_site == PydanticObjectId(test_context.vaccination_site_id)
    assert schedule.vaccination_site_name
    assert not schedule.user_attended
    assert schedule.vaccine is None
