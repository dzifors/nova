from __future__ import annotations

from fastapi import APIRouter
from fastapi import status

from typing import Any

from app.repositories import players as players_repo
from app.api.common import responses
from app.api.common.responses import SuccessResponse

router = APIRouter()

# TODO:
# /v1/players
# /v1/players/{player_id}/status
# /v1/players/{player_id}/stats/{mode}
# /v1/players/{player_id}/stats


@router.get(
    path="/players/count", name="Get player count", description="Get player count"
)
async def handle_get_player_count():
    player_count = players_repo.count()
    return responses.success(content=player_count, status_code=status.HTTP_200_OK)


@router.get(
    path="/players/{player_id}",
    name="Get player",
    description="Get player using provided id",
)
async def handle_get_player(player_id: int) -> SuccessResponse[dict[str, Any]]:
    player = players_repo.get_one(id=player_id)

    if player is None:
        return responses.error(
            message="Player not found", status_code=status.HTTP_404_NOT_FOUND
        )
    return responses.success(content=player, status_code=status.HTTP_200_OK)


@router.get(
    path="/players/{player_id}/stats",
    name="Get player stats",
    description="Get player stats using provided id",
)
async def handle_get_player_stats(player_id: int) -> SuccessResponse[dict[str, Any]]:
    # player = players_repo.get_one(id=player_id)

    # if player is None:
    #     return responses.error(
    #         message="Player not found",
    #         status_code=status.HTTP_404_NOT_FOUND
    #     )

    return responses.error(
        message="Not yet implemented", status_code=status.HTTP_501_NOT_IMPLEMENTED
    )


@router.get(
    path="/players/{player_id}/status",
    name="Get player status",
    description="Get player status using provided id",
)
async def handle_get_player_status(player_id: int) -> SuccessResponse[dict[str, Any]]:
    # player = players_repo.get_one(id=player_id)

    # if player is None:
    #     return responses.error(
    #         message="Player not found",
    #         status_code=status.HTTP_404_NOT_FOUND
    #     )

    return responses.error(
        message="Not yet implemented", status_code=status.HTTP_501_NOT_IMPLEMENTED
    )


@router.get(
    path="/players/{player_id}/stats/{mode}",
    name="Get player stats for mode",
    description="Get player stats for mode using provided id",
)
async def handle_get_player_stats_for_mode(
    player_id: int, mode: str
) -> SuccessResponse[dict[str, Any]]:
    # player = players_repo.get_one(id=player_id)

    # if player is None:
    #     return responses.error(
    #         message="Player not found",
    #         status_code=status.HTTP_404_NOT_FOUND
    #     )

    return responses.error(
        message="Not yet implemented", status_code=status.HTTP_501_NOT_IMPLEMENTED
    )


@router.get(
    path="/players", name="Get multiple players", description="Get multiple players"
)
async def handle_get_players() -> SuccessResponse[dict[str, Any]]:
    # players = players_repo.get_all()

    return responses.error(
        message="Not yet implemented", status_code=status.HTTP_501_NOT_IMPLEMENTED
    )
