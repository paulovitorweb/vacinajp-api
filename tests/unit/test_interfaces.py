import pytest
from pytest_mock import MockerFixture

from src.vacinajp.infrastructure.repository import UnitOfWork


pytestmark = pytest.mark.asyncio


async def test__unit_of_work_instances_should_raise_an_exception(mocker: MockerFixture):
    class ConcreteUnitOfWork(UnitOfWork):
        pass

    with pytest.raises(TypeError):
        ConcreteUnitOfWork(session=None)


async def test__unit_of_work_instances_should_succeed(mocker: MockerFixture):
    class ConcreteUnitOfWork(UnitOfWork):
        def __call__(self):
            pass

    ConcreteUnitOfWork(session=None)
