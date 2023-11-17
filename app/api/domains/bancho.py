""" bancho: handle packets from the osu! client """
from __future__ import annotations

import os
from pathlib import Path
from datetime import date
from time import time
from aiohttp import streamer

from fastapi import APIRouter, status
from fastapi.param_functions import Header
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, HTMLResponse

from typing import Optional, Literal, Mapping, TypedDict

import app.settings
from app.api.common import responses
from app.constants import regexes
from app.types import IPAddress
from app.repositories import players as players_repo

BASE_DOMAIN = app.settings.DOMAIN

BEATMAPS_PATH = os.path.join(app.settings.DATA_DIRECTORY, "osu")

router = APIRouter(tags=[f"Bancho (c.{app.settings.DOMAIN})"])


@router.get(
    path="/",
    name="Bancho web handler",
    description="Handle a request from a web browser",
)
async def handle_browser_request() -> HTMLResponse:
    image_source = "https://media.tenor.com/J9ho96z98BAAAAAC/bugcat-bugcatsticker.gif"
    content = f"""
    <h1>boop</h1>
    <img src={image_source} />
    """
    return HTMLResponse(content=content, status_code=status.HTTP_200_OK)


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

    # player = app.state.sessions.players.get(token=osu_token)

    return responses.error(
        message="Not implemented", status_code=status.HTTP_501_NOT_IMPLEMENTED
    )


class LoginResponse:
    def __init__(self, osu_token: str, response_body: bytes) -> None:
        self.osu_token = osu_token
        self.response_body = response_body


def login(headers: Mapping[str, str], body: bytes, ip: IPAddress) -> LoginResponse:
    """\
    Login has no specific packet, but happens when the osu!
    client sends a request without an 'osu-token' header.

    Request format:
      username\npasswd_md5\nosu_version|utc_offset|display_city|osu_path_md5:adapters_str:adapters_md5:uninstall_md5:disk_signature_md5|pm_private\n

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
    login_data = parse_login_data(body)

    osu_version_is_valid = regexes.OSU_VERSION.match(login_data.osu_version)
    if not osu_version_is_valid:
        return LoginResponse(osu_token="invalid-request", response_body=b"")

    print(osu_version_is_valid["date"][0:4])

    # osu_version = {
    #     "date": date(
    #         year=osu_version_is_valid["date"][0:4],
    #         month=osu_version_is_valid["date"][4:6],
    #         day=osu_version_is_valid["date"][6:8],
    #     ),
    #     "revision": int(osu_version_is_valid["revision"]),
    #     "stream": osu_version_is_valid["stream"],
    # }

    running_under_wine = login_data.adapters_str == "runningunderwine"
    adapters = login_data.adapters_str[:-1].split(".")

    if not (running_under_wine or any(adapters)):
        return LoginResponse(
            osu_token="empty-adapters",
            response_body=(
                app.packets.UserId(-1)
                + app.packets.Notification(
                    "Please restart your osu! and try again. (empty adapters)"
                )
            ),
        )

    login_time = time()

    # player_already_logged_in = app.state.sessions.players.get(
    #     name=login_data["username"]
    # )

    # if player_already_logged_in and osu_version["stream"] != "tourney":
    #     if (login_time - player_already_logged_in.last_recv_time) < 10:
    #         return {
    #             "osu_token": "user-already-logged-in",
    #             "response_body": (
    #                 app.packets.user_id(-1)
    #                 + app.packets.notification("User already logged in.")
    #             ),
    #         }
    #     else:
    #         player_already_logged_in.logout()
    #         del player_already_logged_in

    player_info = players_repo.get_one(name=login_data.username)

    return LoginResponse(
        osu_token="asda",
        response_body=app.packets.UserId(0) + app.packets.Notification("Logged in"),
    )


class LoginData:
    def __init__(
        self,
        username: str,
        password_md5: bytes,
        osu_version: str,
        utc_offset: str,
        display_city: bool,
        pm_private: bool,
        osu_path_md5: str,
        adapters_str: str,
        adapters_md5: str,
        uninstall_md5: str,
        disk_signature_md5: str,
    ) -> None:
        self.username = username
        self.password_md5 = password_md5
        self.osu_version = osu_version
        self.utc_offset = utc_offset
        self.display_city = display_city
        self.pm_private = pm_private
        self.osu_path_md5 = osu_path_md5
        self.adapters_str = adapters_str
        self.adapters_md5 = adapters_md5
        self.uninstall_md5 = uninstall_md5
        self.disk_signature_md5 = disk_signature_md5


def parse_login_data(data: bytes) -> LoginData:
    decoded_data = data.decode().split("\n")

    username = decoded_data[0]
    password_md5 = decoded_data[1]
    client_info = decoded_data[2].split("|")

    osu_version = client_info[0]
    utc_offset = client_info[1]
    display_city = client_info[2]
    client_hashes = client_info[3][:-1].split(":", maxsplit=4)
    pm_private = client_info[4]

    osu_path_md5 = client_hashes[0]
    adapters_str = client_hashes[1]
    adapters_md5 = client_hashes[2]
    uninstall_md5 = client_hashes[3]
    disk_signature_md5 = client_hashes[4]

    return LoginData(
        username=username,
        password_md5=password_md5.encode(),
        osu_version=osu_version,
        utc_offset=utc_offset,
        display_city=display_city == "1",
        pm_private=pm_private == "1",
        osu_path_md5=osu_path_md5,
        adapters_str=adapters_str,
        adapters_md5=adapters_md5,
        uninstall_md5=uninstall_md5,
        disk_signature_md5=disk_signature_md5,
    )
