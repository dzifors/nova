from __future__ import annotations

from fastapi import APIRouter

from . import leaderboard
from . import players

import app.settings

apiv1_router = APIRouter(tags=[f"API v1 (api.{app.settings.DOMAIN}/v1)"], prefix="/v1")

apiv1_router.include_router(players.router)
apiv1_router.include_router(leaderboard.router)