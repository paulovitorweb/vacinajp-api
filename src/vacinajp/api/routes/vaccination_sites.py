import random
import mimesis
from fastapi import APIRouter, Response, status
from src.vacinajp.domain.models import Address, GeoJson2DPoint, VaccinacionSite


vaccination_sites_router = APIRouter()


@vaccination_sites_router.post("/seed")
async def seed_vaccination_sites():
    await seed_vaccination_sites_view()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def seed_vaccination_sites_view():
    count = 50
    data = []
    for _ in range(count):
        person = mimesis.Person()
        address = mimesis.Address(locale='pt-br')

        neighborhoods = [
            'Centro',
            'Cristo Redentor',
            'Mangabeira'
        ]

        data.append(
            VaccinacionSite(
                name=person.full_name(),
                address=Address(
                    street_name=address.street_name(),
                    street_number=address.street_number(),
                    neighborhood=random.choice(neighborhoods)
                ),
                geo=GeoJson2DPoint(
                    coordinates=(address.longitude(), address.latitude())
                )
            )
        )
    await VaccinacionSite.insert_many(data)
