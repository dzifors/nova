from __future__ import annotations

from enum import IntFlag, IntEnum, unique

# from app.utils import escape_enum, pymysql_encode


@unique
# @pymysql_encode(escape_enum)
class Privileges(IntFlag):
    """Server-side user privileges"""

    # privileges intended for all normal players.
    UNRESTRICTED = 1 << 0  # is an unbanned player.
    VERIFIED = 1 << 1  # has logged in to the server in-game.

    # has bypass to low-ceiling anticheat measures (trusted).
    WHITELISTED = 1 << 2

    # donation tiers, receives some extra benefits.
    SUPPORTER = 1 << 4
    PREMIUM = 1 << 5

    # notable users, receives some extra benefits.
    ALUMNI = 1 << 7

    # staff permissions, able to manage server app.state.
    TOURNEY_MANAGER = 1 << 10  # able to manage match state without host.
    NOMINATOR = 1 << 11  # able to manage maps ranked status.
    MODERATOR = 1 << 12  # able to manage users (level 1).
    ADMINISTRATOR = 1 << 13  # able to manage users (level 2).
    OWNER = 1 << 14  # able to manage full server app.state.

    DONATOR = SUPPORTER | PREMIUM
    STAFF = MODERATOR | ADMINISTRATOR | OWNER


@unique
# @pymysql_encode(escape_enum)
class ClientPrivileges(IntFlag):
    """Client privileges for use in-game"""

    PLAYER = 1 << 0
    MODERATOR = 1 << 1
    SUPPORTER = 1 << 2
    OWNER = 1 << 3
    DEVELOPER = 1 << 4
    TOURNAMENT = 1 << 5  # Not used in communications with the osu! client


@unique
# @pymysql_encode(escape_enum)
class ClanPrivileges(IntEnum):
    """Clan member privileges"""

    MEMBER = 1
    OFFICER = 2
    OWNER = 3
