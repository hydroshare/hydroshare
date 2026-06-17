
# --- Dual-app pattern: external (auth) and internal (no-auth) FastAPI apps ---
import asyncio
import logging
import os
import re

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.external import router as external_router

# ...existing code...

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hs_s3_proxy")
DEBUG_HEADERS = os.environ.get("S3_PROXY_DEBUG_HEADERS", "false").lower() == "true"

BACKEND_BUCKET = os.environ.get("S3_BACKEND_BUCKET")
RESOURCE_ID_RE = re.compile(r"^[0-9a-f]{32}$")

# --- External proxy app (auth enforced, fires events) ---
external_app = FastAPI(title="HydroShare S3 Proxy (external)")
external_app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
external_app.include_router(external_router)

# --- Internal proxy app (no auth, fires events) ---
internal_app = FastAPI(title="HydroShare S3 Proxy (internal)")
internal_app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Server(uvicorn.Server):
    def handle_exit(self, sig: int, frame) -> None:
        return super().handle_exit(sig, frame)


async def main():
    server = Server(config=uvicorn.Config(external_app, workers=1, loop="asyncio",
                                          host="0.0.0.0", port=9000, forwarded_allow_ips="*"))
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
