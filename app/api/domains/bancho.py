""" bancho: handle packets from the osu! client """
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter
from fastapi import status
from fastapi.param_functions import Header
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.responses import ORJSONResponse

from typing import Optional
from typing import Literal
from typing import Mapping

import app.settings
from app.api.common import responses
from app.types import IPAddress

BASE_DOMAIN = app.settings.DOMAIN

BEATMAPS_PATH = os.path.join(app.settings.DATA_DIRECTORY, "osu")

router = APIRouter(tags=[f"Bancho (c.{app.settings.DOMAIN})"])


@router.get(
    path="/",
    name="Bancho web handler",
    description="Handle a request from a web browser",
)
async def handle_browser_request() -> RedirectResponse:
    # Yes, this is a rickroll
    return RedirectResponse("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@router.post(
    path="/",
    name="Bancho client handler",
    description="Handle a request from the osu! client",
)
async def handle_client_request(
    request: Request,
    osu_token: Optional[str] = Header(None),
    user_agent: Literal["osu!"] = Header(...),
) -> responses.SuccessResponse:
    ip = app.utils.get_ip_from_headers(request.headers)

    if osu_token is None:
        # The client is performing a login
        request_body = await request.body()
        login_data = login(headers=request.headers, body=request_body, ip=ip)
        return responses.success(content="ni")

    # player = app.state.sessions.players.get(token=osu_token)

    return responses.error(
        message="Not implemented", status_code=status.HTTP_501_NOT_IMPLEMENTED
    )


class LoginResponse:
    osu_token: str
    response_body: bytes


def login(headers: Mapping[str, str], body: bytes, ip: IPAddress) -> LoginResponse:
    """\
    Login has no specific packet, but happens when the osu!
    client sends a request without an 'osu-token' header.

    Request format:
      username\npasswd_md5\nosu_version|utc_offset|display_city|client_hashes|pm_private\n

    Response format:
      Packet 5 (userid), with ID:
      -1: authentication failed
      -2: old client
      -3: banned
      -4: banned
      -5: error occurred
      -6: needs supporter
      -7: password reset
      -8: requires verification
      other: valid id, logged in
    """
    return LoginResponse()


def parse_login_data(data: bytes):
    return
