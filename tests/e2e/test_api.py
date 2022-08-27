import pytest
import base64

from httpx import AsyncClient
from beanie import PydanticObjectId

from src.vacinajp.common.config import Settings
from src.vacinajp.domain.models import VaccinacionSite


pytestmark = pytest.mark.asyncio
settings = Settings()


class BaseUserContext:
    def get_authorization(self) -> str:
        return f'Bearer {self.token}'


class TestUserContext(BaseUserContext):
    user_cpf: str = ''
    user_birth_date: str = ''
    user_id: str = ''
    token: str = ''
    vaccination_site_id: str = ''


class TestProfessionalUserContext(BaseUserContext):
    user_cpf: str = ''
    user_password: str = ''
    user_birth_date: str = ''
    user_id: str = ''
    token: str = ''


class TestAdminContext:
    user_name: str = ''
    user_password: str = ''

    def get_authorization(self) -> str:
        value = f'{settings.admin_username}:{settings.admin_password}'
        return 'Basic ' + base64.b64encode(value.encode()).decode()


test_context = TestUserContext()
test_professional_context = TestProfessionalUserContext()
test_admin_context = TestAdminContext()


async def test__create_user(test_app: AsyncClient):
    payload = {'name': 'Jon Snow', 'cpf': '27677113028', 'birth_date': '1990-03-10'}
    response = await test_app.post('/users/', json=payload)
    assert response.status_code == 201

    json = response.json()
    assert json['name'] == 'Jon Snow'
    assert json['roles'] == []
    assert json['cpf'] == '27677113028'
    assert json['birth_date'] == '1990-03-10'

    assert json['_id'] is not None

    test_context.user_id = json['_id']
    test_context.user_cpf = json['cpf']
    test_context.user_birth_date = json['birth_date']


async def test__user_basic_login(test_app: AsyncClient):
    payload = {'cpf': '27677113028', 'birth_date': '1990-03-10'}
    response = await test_app.post('/users/login', json=payload)
    assert response.status_code == 200

    json = response.json()
    assert json['access_token']
    assert json['token_type'] == 'bearer'

    test_context.token = json['access_token']


async def test__user_me(test_app: AsyncClient):
    response = await test_app.get('/users/me', headers=_get_authorization_headers())
    assert response.status_code == 200

    json = response.json()
    assert json['_id'] == test_context.user_id
    assert json['name'] == 'Jon Snow'
    assert json['roles'] == []
    assert json['cpf'] == '27677113028'
    assert json['birth_date'] == '1990-03-10'

    assert len(json['vaccine_card']) == 0
    assert len(json['schedules']) == 0


async def test__get_available_schedules_from_date(test_app: AsyncClient):
    response = await test_app.get('/calendar/2022/8/1', headers=_get_authorization_headers())
    assert response.status_code == 200
    test_context.vaccination_site_id = response.json()[0]['_id']


async def test__create_schedule(test_app: AsyncClient):
    body = {'date': '2022-08-01', 'vaccination_site': test_context.vaccination_site_id}
    response = await test_app.post('/schedules', headers=_get_authorization_headers(), json=body)
    assert response.status_code == 201

    json = response.json()
    assert json['_id'] is not None
    assert json['user'] == test_context.user_id
    assert json['date'] == '2022-08-01'
    assert json['vaccination_site'] == test_context.vaccination_site_id
    assert json['vaccination_site_name'] == getattr(
        await VaccinacionSite.get(PydanticObjectId(test_context.vaccination_site_id)), 'name'
    )
    assert json['user_attended'] is False
    assert json['vaccine'] is None


async def test__user_me_should_return_schedule(test_app: AsyncClient):
    response = await test_app.get('/users/me', headers=_get_authorization_headers())
    assert response.status_code == 200

    json = response.json()
    assert len(json['vaccine_card']) == 0
    assert len(json['schedules']) == 1
    assert json['schedules'][0]['user_attended'] is False
    assert json['schedules'][0]['vaccine'] is None


async def test__create_user_to_be_professional(test_app: AsyncClient):
    payload = {'name': 'Daenerys Targaryen', 'cpf': '27677113029', 'birth_date': '1990-03-15'}
    response = await test_app.post('/users/', json=payload)
    assert response.status_code == 201

    json = response.json()
    test_professional_context.user_id = json['_id']
    test_professional_context.user_cpf = json['cpf']
    test_professional_context.user_birth_date = json['birth_date']


async def test__admin_set_role_to_user(test_app: AsyncClient):
    payload = {'roles': ['HEALTHCARE_PROFESSIONAL']}
    headers = {'Authorization': test_admin_context.get_authorization()}
    response = await test_app.patch(
        f'/admin/users/{test_professional_context.user_id}/roles', json=payload, headers=headers
    )
    assert response.status_code == 200


async def test__basic_login_for_professional_user_should_not_succeed(test_app: AsyncClient):
    payload = {
        'cpf': test_professional_context.user_cpf,
        'birth_date': test_professional_context.user_birth_date,
    }
    response = await test_app.post('/users/login', json=payload)
    assert response.status_code == 403


async def test__admin_generate_password(test_app: AsyncClient):
    headers = {'Authorization': test_admin_context.get_authorization()}
    response = await test_app.patch(
        f'/admin/users/{test_professional_context.user_id}/generate-password', headers=headers
    )
    assert response.status_code == 200
    test_professional_context.user_password = response.json()['password']


async def test__staff_login(test_app: AsyncClient):
    payload = {
        'cpf': test_professional_context.user_cpf,
        'password': test_professional_context.user_password,
    }
    response = await test_app.post('/users/login/staff', json=payload)
    assert response.status_code == 200

    json = response.json()
    assert json['access_token']
    assert json['token_type'] == 'bearer'

    test_professional_context.token = json['access_token']


async def test__create_vaccine(test_app: AsyncClient):
    headers = {'Authorization': test_professional_context.get_authorization()}
    payload = {
        'user': test_context.user_id,
        'date': '2022-08-01',
        'vaccination_site': test_context.vaccination_site_id,
        'dose': 1,
        'laboratory': 'PFIZER',
    }
    response = await test_app.post('/vaccines', json=payload, headers=headers)
    assert response.status_code == 201


async def test__user_me_should_return_vaccine_card_and_modified_schedule(test_app: AsyncClient):
    response = await test_app.get('/users/me', headers=_get_authorization_headers())
    assert response.status_code == 200

    json = response.json()
    assert len(json['vaccine_card']) == 1
    assert len(json['schedules']) == 1
    assert json['schedules'][0]['user_attended'] is True
    assert json['schedules'][0]['vaccine'] is not None


def _get_authorization_headers():
    return {'Authorization': test_context.get_authorization()}
