from __future__ import annotations

from enum import IntEnum, unique

from app.objects.score import Grade
from app.utils import escape_enum, pymysql_encode


@unique
@pymysql_encode(escape_enum)
class PresenceFilter(IntEnum):
    """osu! client side filter for which users the player can see."""

    Nil = 0
    All = 1
    Friends = 2


@unique
@pymysql_encode(escape_enum)
class Action(IntEnum):
    """The client's current app.state."""

    Idle = 0
    Afk = 1
    Playing = 2
    Editing = 3
    Modding = 4
    Multiplayer = 5
    Watching = 6
    Unknown = 7
    Testing = 8
    Submitting = 9
    Paused = 10
    Lobby = 11
    Multiplaying = 12
    OsuDirect = 13


class ModeData:
    """A player's stats in a single gamemode."""

    tscore: int
    rscore: int
    pp: int
    acc: float
    plays: int
    playtime: int
    max_combo: int
    total_hits: int
    rank: int  # global

    grades: dict[Grade, int]  # XH, X, SH, S, A
