import asyncio
import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.external import router as external_router, s3_proxy
from api.lib.event_service import close_event_service_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hs_s3_proxy")


def _parse_allow_origins() -> list[str]:
    raw = os.environ.get("CORS_ALLOW_ORIGINS", "*").strip()
    if not raw:
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(title="HydroShare S3 Proxy")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(external_router)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await s3_proxy.close()
    close_event_service_client()


class Server(uvicorn.Server):
    def handle_exit(self, sig: int, frame) -> None:
        return super().handle_exit(sig, frame)


async def main():
    server = Server(
        config=uvicorn.Config(
            app, workers=1, loop="asyncio",
            host="0.0.0.0", port=9000, forwarded_allow_ips="*"
        )
    )
    api = asyncio.create_task(server.serve())
    await asyncio.wait([api])


if __name__ == "__main__":
    asyncio.run(main())
