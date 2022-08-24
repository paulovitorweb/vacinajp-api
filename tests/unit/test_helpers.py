import pytest
from datetime import datetime
from pytest_mock import MockerFixture
from passlib.context import CryptContext
from jose import exceptions as jwt_exceptions

from src.vacinajp.common.helpers import DateHelper, JwtHelper, SecurityHelper


pytestmark = pytest.mark.asyncio


async def test__helper_get_password_hash(mocker: MockerFixture):
    mocker.patch.object(CryptContext, 'hash', return_value='hashed_password')
    assert SecurityHelper.get_password_hash('plain_password') == 'hashed_password'


async def test__helper_verify_password_should_return_false(mocker: MockerFixture):
    mocker.patch.object(CryptContext, 'verify', return_value=False)
    assert SecurityHelper.verify_password('plain', 'hashed') is False


async def test__helper_create_access_token(mocker: MockerFixture):
    mocker.patch.object(CryptContext, 'verify', return_value=True)
    assert SecurityHelper.verify_password('plain', 'hashed') is True


async def test__helper_create_access_token_should_return_encoded_token(
    mocker: MockerFixture,
):
    mocker.patch.object(DateHelper, 'utcnow', return_value=datetime(2022, 8, 21))
    kwargs_mock = {'jwt_token_expire': 15, 'jwt_secret_key': 'secret_key'}
    mocker.patch(f'{JwtHelper.__module__}.settings', **kwargs_mock)

    access_token = JwtHelper.create_access_token(data={'sub': 'abcd1234'})

    assert access_token == (
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYmNkMTIzNCIsImV4cCI6MTY2MTA0MDkwMH0.'
        'QoVzwyoRJMiGSCvU7m-yw4mWqVFvrJH5A0vnzKOpinE'
    )


async def test__helper_jwt_create_and_decode_should_return_original_data(mocker: MockerFixture):
    access_token = JwtHelper.create_access_token(data={'sub': 'abcd1234'})
    payload = JwtHelper.decode_access_token(access_token)
    assert payload.get('sub') == 'abcd1234'


async def test__helper_jwt_create_and_decode_payload_should_includes_exp(mocker: MockerFixture):
    access_token = JwtHelper.create_access_token(data={'sub': 'abcd1234'})
    assert 'exp' in JwtHelper.decode_access_token(access_token)


async def test__helper_jwt_should_raises_an_exception(mocker: MockerFixture):
    kwargs_mock = {'jwt_token_expire': -1, 'jwt_secret_key': 'secret_key'}
    mocker.patch(f'{JwtHelper.__module__}.settings', **kwargs_mock)
    access_token = JwtHelper.create_access_token(data={'sub': 'abcd1234'})
    with pytest.raises(jwt_exceptions.ExpiredSignatureError):
        JwtHelper.decode_access_token(access_token)


async def test__helper_utcnow(mocker: MockerFixture):
    mock_now = mocker.patch(f'{JwtHelper.__module__}.datetime')
    mock_now.utcnow.return_value = datetime(2022, 8, 21)
    mock_now.side_effect = lambda *args, **kw: datetime(*args, **kw)

    assert DateHelper.utcnow() == datetime(2022, 8, 21)
