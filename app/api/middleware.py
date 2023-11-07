from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.requests import ClientDisconnect
from starlette.responses import Response

import time

from app.logging import Colors
from app.logging import log
from app.logging import format_time_magnitude
from app.logging import print_color


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter_ns()
        response = await call_next(request)
        end_time = time.perf_counter_ns()

        time_elapsed = end_time - start_time

        color = (
            Colors.GREEN
            if 200 <= response.status_code < 300
            else Colors.YELLOW
            if 300 <= response.status_code < 400
            else Colors.RED
        )

        try:
            url = f"{request.headers['host']}{request['path']}"
        except KeyError:
            # If host is not set, reject the request
            url = f"{request['path']}"

        log(f"[{request.method}] {response.status_code} {url}", color, end=" | ")
        print_color(f"Request took: {format_time_magnitude(time_elapsed)}", Colors.BLUE)

        response.headers["X-Process-Time"] = str(round(time_elapsed) / 1e6)
        return response


class ClientDisconnectHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # if an osu! client is waiting on leaderboard data
        # and switches to another leaderboard, it will cancel
        # the previous request midway, resulting in a large
        # error in the console. this is to catch that :)

        try:
            return await call_next(request)
        except ClientDisconnect:
            # client disconnected from the server
            # while we were sending the response
            return Response("Client disconnected")
        except RuntimeError as exc:
            if exc.args[0] == "No response returned.":
                # client disconnected from the server
                # while we were sending the response
                return Response("Client disconnected")

            # unrelated issue, raise normally
            raise exc
