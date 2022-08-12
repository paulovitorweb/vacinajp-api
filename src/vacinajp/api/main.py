from fastapi import FastAPI


from .routes import vaccination_sites_router, calendar_router, schedule_router, users_router, vaccine_router, admin_router
from src.vacinajp.infrastructure.mongo_client import client


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    await client.initialize()
    app.include_router(vaccination_sites_router, prefix="/vaccination-sites", tags=["vaccination_sites"])
    app.include_router(calendar_router, prefix="/calendar", tags=["calendar"])
    app.include_router(schedule_router, prefix="/schedules", tags=["schedules"])
    app.include_router(users_router, prefix="/users", tags=["users"])
    app.include_router(vaccine_router, prefix="/vaccines", tags=["vaccines"])
    app.include_router(admin_router, prefix="/admin", tags=["admin"])