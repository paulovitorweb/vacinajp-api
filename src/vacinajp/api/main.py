from fastapi import FastAPI

from src.vacinajp.api import routes
from src.vacinajp.infrastructure.mongo_client import client


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    await client.initialize()
    app.include_router(
        routes.vaccination_sites_router, prefix="/vaccination-sites", tags=["vaccination_sites"]
    )
    app.include_router(routes.calendar_router, prefix="/calendar", tags=["calendar"])
    app.include_router(routes.schedule_router, prefix="/schedules", tags=["schedules"])
    app.include_router(routes.users_router, prefix="/users", tags=["users"])
    app.include_router(routes.vaccine_router, prefix="/vaccines", tags=["vaccines"])
    app.include_router(routes.admin_router, prefix="/admin", tags=["admin"])
