""" osu: handle connections from web, api and more? """
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from fastapi.param_functions import Query

import app.settings

router = APIRouter(tags=[f"osu! Web API (osu.{app.settings.DOMAIN})"])


@router.get(
    path="/web/bancho_connect.php",
    name="Bancho Connect",
    description="Bancho connect endpoint, not implemented",
)
async def handle_bancho_connect(
    # NOTE: this is disabled as this endpoint can be called
    #       before a player has been granted a session
    # player: Player = Depends(authenticate_player_session(Query, "u", "h")),
    osu_ver: str = Query(..., alias="v"),
    active_endpoint: Optional[str] = Query(None, alias="fail"),
    net_framework_vers: Optional[str] = Query(None, alias="fx"),  # delimited by |
    client_hash: Optional[str] = Query(None, alias="ch"),
    retrying: Optional[bool] = Query(None, alias="retry"),  # '0' or '1'
):
    print(osu_ver)
    print(active_endpoint)
    print(net_framework_vers)
    print(client_hash)
    print(retrying)
    return b""  # TODO
