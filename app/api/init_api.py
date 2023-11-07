from __future__ import annotations

import asyncio
import os
from pprint import pprint
from typing import Any
from typing import Literal

import aiohttp
import orjson
from fastapi import status
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.requests import Request
import starlette.routing

import app.settings
import app.state
from app.api import api_router
from app.api import domains
from app.api import middleware
from app.api.common import responses
from app.logging import log
from app.logging import Colors

import MySQLdb
import MySQLdb.cursors


class BanchoAPI(FastAPI):
    def openapi(self) -> dict[str, Any]:
        if not self.openapi_schema:
            routes = self.routes
            starlette_hosts = [
                host
                for host in super().routes
                if isinstance(host, starlette.routing.Host)
            ]

            # XXX:HACK fastapi will not show documentation for routes
            # added through use sub applications using the Host class
            # (e.g. app.host('other.domain', app2))
            for host in starlette_hosts:
                for route in host.routes:
                    if route not in routes:
                        routes.append(route)

            self.openapi_schema = get_openapi(
                title=self.title,
                version=self.version,
                openapi_version=self.openapi_version,
                description=self.description,
                terms_of_service=self.terms_of_service,
                contact=self.contact,
                license_info=self.license_info,
                routes=routes,
                tags=self.openapi_tags,
                servers=self.servers,
                lifespan=self.lifespan,
            )

        return self.openapi_schema


def init_routes(asgi_app: BanchoAPI):
    """Initialize all routes"""
    domain = app.settings.DOMAIN

    for subdomain in ("c", "ce", "c4", "c5", "c6"):
        asgi_app.host(f"{subdomain}.{domain}", domains.bancho.router)

    asgi_app.host(f"a.{domain}", domains.avatars.router)
    asgi_app.host(f"osu.{domain}", domains.osu.router)

    asgi_app.host(f"api.{domain}", api_router)


def init_exception_handlers(asgi_app: BanchoAPI) -> None:
    @asgi_app.exception_handler(status.HTTP_404_NOT_FOUND)
    async def handle_not_found_error(
        request: Request, exc: Literal[404]
    ) -> responses.ErrorResponse:
        return responses.error(
            message="Not found", status_code=status.HTTP_404_NOT_FOUND
        )

    @asgi_app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> responses.ErrorResponse:
        log(f"Validation error on {request.url}", Colors.RED)
        pprint(exc.errors())

        return responses.error(
            message=jsonable_encoder(exc.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def init_middleware(asgi_app: BanchoAPI):
    """Initialize all necessary middlewares"""
    asgi_app.add_middleware(middleware.LoggingMiddleware)
    asgi_app.add_middleware(middleware.ClientDisconnectHandlerMiddleware)

    asgi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


async def lifespan(asgi_app: FastAPI):
    app.state.loop = asyncio.get_running_loop()

    if os.geteuid() == 0:
        log(
            "Running the server with root privileges is not recommended.",
            Colors.RED,
        )

    app.state.services.http_client = aiohttp.ClientSession(
        json_serialize=lambda x: orjson.dumps(x).decode(),
    )

    try:
        app.state.services.database = MySQLdb.connect(
            host=app.settings.MYSQL_HOST,
            port=app.settings.MYSQL_PORT,
            user=app.settings.MYSQL_USERNAME,
            password=app.settings.MYSQL_PASSWORD,
            database=app.settings.MYSQL_DATABASE,
        )
        log("Connected to MySQL", Colors.GREEN)
    except:
        log("MySQL Connection Failed", Colors.RED)
    # await app.state.services.redis.initialize()

    # # if app.state.services.datadog is not None:
    #     app.state.services.datadog.start(
    #         flush_in_thread=True,
    #         flush_interval=15,
    #     )
    #     app.state.services.datadog.gauge("bancho.online_players", 0)

    # app.state.services.ip_resolver = app.state.services.IPResolver()

    # await app.state.services.run_sql_migrations()

    # async with app.state.services.database.connection() as db_conn:
    #     await collections.initialize_ram_caches(db_conn)

    # await app.bg_loops.initialize_housekeeping_tasks()

    log("Startup process complete.", Colors.GREEN)
    log(
        f"Listening @ {app.settings.SERVER_ADDRESS}:{app.settings.SERVER_PORT}",
        Colors.MAGENTA,
    )

    yield

    await app.state.services.http_client.close()
    app.state.services.database.close()

    log("Server shut down successfully, thank you for using bancho", Colors.MAGENTA)


def init_api():
    asgi_app = BanchoAPI(
        title="nova.py",
        summary="Like bancho.py, but betterer(TM)",
        terms_of_service=f"https://{app.settings.DOMAIN}/docs/tos",
        version=app.settings.VERSION,
        lifespan=lifespan,
    )

    init_middleware(asgi_app)
    init_exception_handlers(asgi_app)
    init_routes(asgi_app)

    return asgi_app


asgi_app = init_api()
