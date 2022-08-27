from datetime import datetime
import pytest

from bson import ObjectId
from beanie import PydanticObjectId

from src.vacinajp.common.config import Settings
from src.vacinajp.common.errors import UserAlreadyExists
from src.vacinajp.domain.models import User, UserInfo, Schedule, Vaccine, VaccineLaboratory
from src.vacinajp.infrastructure.mongo_repository import MongoUserRepository


pytestmark = pytest.mark.asyncio
settings = Settings()


class TestContext:
    user_id: PydanticObjectId


async def test__user_repository_create_should_succeed(db_test, session_test):
    user = User(name='Jon Snow', cpf='96416083043', birth_date='1980-05-10')
    created_user = await MongoUserRepository(session_test).create(user)
    user_from_db = await db_test['users'].find_one({'cpf': created_user.cpf})
    assert user_from_db['cpf'] == '96416083043'


async def test__user_repository_create_should_raise_an_exception(db_test, session_test):
    user = User(name='Ted Mosby', cpf='96416083043', birth_date='1970-05-10')
    with pytest.raises(UserAlreadyExists):
        await MongoUserRepository(session_test).create(user)


async def test__user_repository_get(db_test, session_test):
    user_from_db = await db_test['users'].find_one({'cpf': '96416083043'})
    existing_user = await MongoUserRepository(session_test).get(user_from_db['_id'])
    assert isinstance(existing_user, User)
    assert existing_user.id == user_from_db['_id']


async def test__user_repository_get_from_cpf(db_test, session_test):
    user_from_db = await db_test['users'].find_one({'cpf': '96416083043'})
    existing_user = await MongoUserRepository(session_test).get_from_cpf('96416083043')
    assert isinstance(existing_user, User)
    assert existing_user.id == user_from_db['_id']


async def test__user_repository_update(db_test, session_test):
    repo = MongoUserRepository(session_test)
    user = await repo.get_from_cpf('96416083043')
    user.name = 'King of North'
    await repo.update(user)
    user_from_db = await db_test['users'].find_one({'cpf': '96416083043'})
    assert user_from_db['name'] == 'King of North'


async def test__user_repository_get_user_info_without_schedules_and_vaccine_card(
    db_test, session_test
):
    user_from_db = await db_test['users'].find_one({'cpf': '96416083043'})
    user_info = await MongoUserRepository(session_test).get_user_info(user_from_db['_id'])
    assert isinstance(user_info, UserInfo)
    assert user_info.cpf == '96416083043'
    assert len(user_info.schedules) == 0
    assert len(user_info.vaccine_card) == 0


async def test__user_repository_get_user_info_with_schedules_and_vaccine_card(
    db_test, session_test
):
    user_from_db = await db_test['users'].find_one({'cpf': '96416083043'})
    await _insert_schedule_and_vaccine_to_user(user_from_db['_id'], session_test)
    user_info = await MongoUserRepository(session_test).get_user_info(user_from_db['_id'])
    assert isinstance(user_info, UserInfo)
    assert user_info.cpf == '96416083043'
    assert len(user_info.schedules) == 1
    assert len(user_info.vaccine_card) == 1


async def _insert_schedule_and_vaccine_to_user(user_id, session_test):
    schedule = Schedule(
        user=user_id,
        date=datetime(2022, 8, 1),
        vaccination_site=PydanticObjectId('630a44640706d38696819294'),
        vaccination_site_name='Test',
    )
    vaccine = Vaccine(
        user=user_id,
        date=datetime(2022, 8, 1),
        vaccination_site=PydanticObjectId('630a44640706d38696819294'),
        vaccination_site_name='Test',
        dose=1,
        laboratory=VaccineLaboratory.CORONAVAC,
        professional=PydanticObjectId('630a4601c08a4914c36aefcb'),
    )
    await schedule.create(session=session_test)
    await vaccine.create(session=session_test)
