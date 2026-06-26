from __future__ import annotations

from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.schema_health import KB_SCHEMA_SETUP_GUIDE, safe_find_missing_kb_tables
from app.db.session import engine

configure_logging(settings.log_level)
logger = get_logger("app.main")


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info(
            "Starting FastAPI app name=%s version=%s log_level=%s",
            settings.app_name,
            settings.app_version,
            settings.log_level.upper(),
        )
        missing_tables = safe_find_missing_kb_tables(engine)
        if missing_tables is None:
            logger.warning("Knowledge base schema check skipped because the database is unavailable.")
        elif missing_tables:
            logger.warning(
                "Knowledge base schema is not ready missing_tables=%s. %s",
                ",".join(missing_tables),
                KB_SCHEMA_SETUP_GUIDE,
            )
        else:
            logger.info("Knowledge base schema check passed.")
        yield
        logger.info("Shutting down FastAPI app name=%s", settings.app_name)

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        started = perf_counter()
        client_host = request.client.host if request.client else "-"
        path = request.url.path
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (perf_counter() - started) * 1000
            logger.exception(
                "Unhandled request error method=%s path=%s client=%s duration_ms=%.2f",
                request.method,
                path,
                client_host,
                duration_ms,
            )
            raise

        matched_route = request.scope.get("route")
        route_template = getattr(matched_route, "path", path)
        duration_ms = (perf_counter() - started) * 1000
        status_code = response.status_code
        if status_code >= 500:
            log_method = logger.error
        elif status_code >= 400:
            log_method = logger.warning
        else:
            log_method = logger.info

        log_method(
            "HTTP request method=%s path=%s route=%s status=%s client=%s duration_ms=%.2f",
            request.method,
            path,
            route_template,
            status_code,
            client_host,
            duration_ms,
        )
        return response

    @application.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {
            "message": "鎶曟爣鏂囨。鍔╂墜鎺ュ彛",
            "phase": "rag-mvp",
            "frontend": "/frontend",
        }

    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
