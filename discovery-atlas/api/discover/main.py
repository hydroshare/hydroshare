import os
import subprocess

from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from discover.app.routers.discovery import router as discovery_router
from discover.config import get_settings

# TODO: get oauth working with swagger/redoc
# Setting the base url for swagger docs
# https://github.com/tiangolo/fastapi/pull/1547
# https://swagger.io/docs/specification/api-host-and-base-path/ma
# https://fastapi.tiangolo.com/how-to/configure-swagger-ui/
# https://github.com/tiangolo/fastapi/pull/499

app = FastAPI(servers=[{"url": get_settings().vite_app_api_url}])

origins = [get_settings().allow_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    discovery_router,
    prefix="/api/discovery",
    tags=["discovery"],
)

@app.on_event("startup")
async def on_startup():
    app.db = AsyncIOMotorClient(get_settings().mongo_url)
    app.mongodb = app.db[get_settings().mongo_database]

