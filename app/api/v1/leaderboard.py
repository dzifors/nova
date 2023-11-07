from __future__ import annotations

import time

from fastapi import APIRouter
from fastapi import status
from fastapi.param_functions import Query

from typing import Any
from typing import Literal
from typing import Optional

import app.state
from app.constants.gamemodes import GameMode
from app.api.common import responses

router = APIRouter()


@router.get(path="/leaderboard", name="Get Leaderboard", description="Get leaderboard")
async def handle_get_leaderboard(
    sort: Literal["tscore", "rscore", "pp", "acc", "plays", "playtime"] = "pp",
    mode_arg: int = Query(0, alias="mode", ge=0, le=11),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, min=0, max=2_147_483_647),
    country: Optional[str] = Query(None, min_length=2, max_length=2),
):
    if mode_arg in (
        GameMode.RELAX_MANIA,
        GameMode.AUTOPILOT_CATCH,
        GameMode.AUTOPILOT_TAIKO,
        GameMode.AUTOPILOT_MANIA,
    ):
        return responses.error(
            message="Invalid gamemode", status_code=status.HTTP_400_BAD_REQUEST
        )

    mode = GameMode(mode_arg)

    query = f"""
        SELECT u.id as player_id, u.name, u.country, s.tscore, s.rscore,
        s.pp, s.plays, s.playtime, s.acc, s.max_combo, 
        s.xh_count, s.x_count, s.sh_count, s.s_count, s.a_count, 
        c.id as clan_id, c.name as clan_name, c.tag as clan_tag 
        FROM stats s 
        LEFT JOIN users u ON s.id = u.id
        LEFT JOIN clans c ON u.clan_id = c.id 
        WHERE u.priv & 1 AND s.{sort} > 0 AND s.mode = %(mode)s
    """

    params: dict[str, Any] = {"mode": mode}

    if country is not None:
        query += "AND u.country = %(country)s"
        params["country"] = country

    query += f"ORDER BY s.{sort} DESC LIMIT %(offset)s, %(limit)s"
    params["offset"] = offset
    params["limit"] = limit

    cursor = app.state.services.database.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()

    leaderboard = []

    for user in result:
        u = {
            "id": user[0],
            "name": user[1],
            "country": user[2],
            "total_score": user[3],
            "ranked_score": user[4],
            "pp": user[5],
            "plays": user[6],
            "playtime": user[7],
            "acc": user[8],
            "max_combo": user[9],
            "xh_count": user[10],
            "x_count": user[11],
            "sh_count": user[12],
            "s_count": user[13],
            "a_count": user[14],
            "clan": {
                "id": user[15],
                "name": user[16],
                "tag": user[17],
            },
        }
        leaderboard.append(u)

    return responses.success(content=leaderboard)
