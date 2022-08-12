import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestContext:
    user_id: str


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
