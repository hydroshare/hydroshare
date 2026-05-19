import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("hs_s3_proxy")

ROUTER_MODE_ENV = "S3_PROXY_ROUTER_MODE"
DEFAULT_ROUTER_MODE = "external"


def _get_router_mode() -> str:
    mode = os.environ.get(ROUTER_MODE_ENV, DEFAULT_ROUTER_MODE).strip().lower()
    if mode not in {"external", "internal"}:
        raise ValueError(
            "Invalid {} value: {}. Expected one of: external, internal".format(
                ROUTER_MODE_ENV, mode
            )
        )
    return mode


def _cors_settings() -> tuple[list[str], bool]:
    raw_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    if not origins:
        return ["*"], False
    return origins, True


def create_app() -> FastAPI:
    mode = _get_router_mode()
    app = FastAPI(title="HydroShare S3 Proxy ({})".format(mode))

    cors_origins, cors_credentials = _cors_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if mode == "external":
        from api.routes.external import router
    else:
        from api.routes.internal import router

    app.include_router(router)
    logger.info("Loaded S3 proxy router mode: %s", mode)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "9000")),
        workers=1,
        loop="asyncio",
        forwarded_allow_ips="*",
    )
