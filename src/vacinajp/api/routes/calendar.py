import calendar
import datetime
from fastapi import APIRouter, Response, status
from src.vacinajp.domain.models import VaccinacionSite, Calendar


calendar_router = APIRouter()


@calendar_router.post("/seed", response_class=Response)
async def seed_calendar(year: int, month: int, schedules: int = 100):
    await seed_calendar_view(year, month, schedules)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@calendar_router.get("/{year}/{month}/{day}/vaccination-sites")
async def get_available_sites_to_schedule_from_date(year: int, month: int, day: int):
    return await get_available_sites_to_schedule_from_date_view(year=year, month=month, day=day)


async def seed_calendar_view(year: int, month: int, schedules: int):
    data = []
    vaccination_sites = await VaccinacionSite.find_all().to_list()
    for date in calendar.Calendar().itermonthdates(year, month):
        if date.month != month:
            continue
        for vaccination_site in vaccination_sites:
            data.append(
                Calendar(
                    date=date,
                    vaccination_site=vaccination_site.id,
                    is_available=True,
                    total_schedules=schedules,
                    remaining_schedules=schedules
                )
            )
    await Calendar.insert_many(data)


async def get_available_sites_to_schedule_from_date_view(year: int, month: int, day: int):
    filters = [
        Calendar.date == datetime.date(year=year, month=month, day=day),
        Calendar.remaining_schedules > 0,
        Calendar.is_available == True
    ]
    available_sites = await Calendar.find(*filters).aggregate([
        # Pesquisa os dados dos locais de vacinação
        {"$lookup": {
            "from": "vaccination_sites",
            "localField": "vaccination_site",
            "foreignField": "_id",
            "as": "vaccination_site_info"
        }},
        {"$unwind": "$vaccination_site_info"},

        # Projeção final
        {"$project": {
            "_id": "$vaccination_site_info._id",
            "name": "$vaccination_site_info.name",
            "address": "$vaccination_site_info.address",
            "geo": "$vaccination_site_info.geo"
        }}
    ], projection_model=VaccinacionSite).to_list()
    return available_sites
