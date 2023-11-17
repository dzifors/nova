from __future__ import annotations
from dataclasses import dataclass
from datetime import date

from enum import Enum, IntEnum, unique
from functools import cached_property
import time

from typing import Any, TypedDict
import uuid
import app.packets as Packets
from app.constants.gamemodes import ALLOWED_GAMEMODES, GameMode
from app.constants.mods import Mods
from app.logging import Colors, log

from app.objects.score import Grade
from app.constants.privileges import ClientPrivileges, Privileges
from app.settings import DOMAIN
import app.state.sessions as Sessions
from app.state.services import database
from app.types import IPAddress

# from app.utils import escape_enum, pymysql_encode


__all__ = ("ModeData", "Status", "Player")


@unique
# @pymysql_encode(escape_enum)
class PresenceFilter(IntEnum):
    """osu! client side filter for which users the player can see."""

    Nil = 0
    All = 1
    Friends = 2


@unique
# @pymysql_encode(escape_enum)
class Action(IntEnum):
    """The client's current in-game action"""

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


@dataclass
class ModeData:
    """A player's stats in a single gamemode."""

    total_score: int
    ranked_score: int
    pp: int
    acc: float
    playcount: int
    playtime: int
    max_combo: int
    total_hits: int
    rank: int  # global

    grades: dict[Grade, int]  # XH, X, SH, S, A


@dataclass
class Status:
    """Current user status"""

    action: Action = Action.Idle
    action_info: str = ""
    map_md5: str = ""
    mods: Mods = Mods.NOMOD
    mode: GameMode = GameMode.VANILLA_OSU
    map_id: int = 0


class LastNp(TypedDict):
    beatmap: Beatmap
    mode: int
    timeout: float


class OsuStream(str, Enum):
    STABLE = "stable"
    BETA = "beta"
    CUTTING_EDGE = "cuttingedge"
    TOURNEY = "tourney"
    DEV = "dev"


class OsuVersion:
    def __init__(self, date: date, revision: int | None, stream: OsuStream) -> None:
        self.date = date
        self.revision = revision
        self.stream = stream


class ClientDetails:
    def __init__(
        self,
        osu_version: OsuVersion,
        osu_path_md5: str,
        adapters_md5: str,
        uninstall_md5: str,
        disk_signature_md5: str,
        adapters: list[str],
        ip: IPAddress,
    ) -> None:
        self.osu_version = osu_version
        self.osu_path_md5 = osu_path_md5
        self.adapters_md5 = adapters_md5
        self.uninstall_md5 = uninstall_md5
        self.disk_signature_md5 = disk_signature_md5
        self.adapters = adapters
        self.ip = ip

    @cached_property
    def client_hash(self) -> str:
        return (
            f"{self.osu_path_md5}:{'.'.join(self.adapters)}."
            f":{self.adapters_md5}:{self.uninstall_md5}:{self.disk_signature_md5}:"
        )


class Player:
    """
    Server-side representation of a player

    Attributes:
    -----------
    token: `str`
        The player's unique token that's used to communicate with the osu! client

    safe_name: `str`
        The player's username, converted to lowercase and spaces replaced with underscores

    pm_private: `bool`
        Whether the player is blocking PMs from non-friends

    silence_end: `int`
        The UNIX timestamp the player's silence ends at

    presence_filter: `PresenceFilter`
        The scope of users the client can see

    bot_client: `bool`
        Whether the player is a bot account

    tournament_client: `bool`
        Whether this is a tournament client

    queue: `bytearray`
        Bytes enqueued to the player which will be transmitted at the tail end of their next connection to the server
    """

    def __init__(
        self, id: int, name: str, privileges: int | Privileges, **extras: Any
    ) -> None:
        self.id = id
        self.name = name
        self.safe_name = self.make_safe_name(self.name)

        if "password_bcrypt" in extras:
            self.password_bcrypt: bytes | None = extras["password_bcrypt"]
        else:
            self.password_bcrypt = None

        token = extras.get("token", None)
        if token is not None and isinstance(token, str):
            self.token = token
        else:
            self.token = self.generate_token()

        if isinstance(privileges, Privileges):
            self.privileges = privileges
        else:
            self.privileges = Privileges(privileges)

        self.stats: dict[GameMode, ModeData] = {}
        self.status: Status = Status()

        self.friends: set[int] = set()
        self.blocks: set[int] = set()

        self.channels: list[Channel] = []
        self.spectators: list[Player] = []
        self.spectating: Player | None = None
        self.match: Match | None
        self.stealth_mode: bool = False

        self.clan: Clan | None = extras.get("clan", None)
        self.clan_privileges: ClanPrivileges | None = extras.get(
            "clan_privileges", None
        )

        self.geolocation: Geolocation = extras.get(
            "geolocation",
            {
                "latitude": 0.0,
                "longitude": 0.0,
                "country": {"acronym": "xx", "numeric": 0},
            },
        )

        self.utc_offset = extras.get("utc_offset", 0)
        self.pm_private = extras.get("pm_private", False)
        self.away_message: str | None = None
        self.silence_end = extras.get("silence_end", 0)
        self.donor_end = extras.get("donor_end", 0)
        self.in_lobby = False

        self.client_details: ClientDetails | None = extras.get("client_details", None)
        self.presence_filter = PresenceFilter.Nil

        self.login_time = extras.get("login_time", 0.0)
        self.last_received_time = self.login_time

        self.recent_scores: dict[GameMode, Score | None] = {
            mode: None for mode in GameMode
        }

        self.last_np: LastNp | None = None
        self.bot_client = extras.get("bot_client", False)
        if self.bot_client:
            self.enqueue_packet = lambda x: None

        self.tournament_client = extras.get("tournament_client", False)

        self.api_key = extras.get("api_key", None)

        self._queue = bytearray()

    def __repr__(self) -> str:
        return f"<{self.name} (id: {self.id})"

    @property
    def is_online(self) -> bool:
        """Returns true if user has a token (is online)"""
        return self.token != ""

    @property
    def url(self) -> str:
        """User's profile URL"""
        return f"https://{DOMAIN}/u/{self.id}"

    @property
    def osu_embed(self) -> str:
        """User's embed for use in osu! chats"""
        return f"[{self.url} {self.name}]"

    @property
    def avatar_url(self) -> str:
        """User's avatar URL"""
        return f"https://a.{DOMAIN}/{self.id}"

    @property
    def full_name(self) -> str:
        """User's full name (clan + username)"""
        if self.clan:
            return f"[{self.clan.tag}] {self.name}"
        else:
            return self.name

    @property
    def remaining_silence(self) -> int:
        """Remaining duration of user's silence"""
        return max(0, int(self.silence_end - time.time()))

    @property
    def is_silenced(self) -> bool:
        """Whether the user is silenced or not"""
        return self.remaining_silence != 0

    @cached_property
    def bancho_privileges(self) -> ClientPrivileges:
        """User's client-side privileges for use in-game"""
        to_return = ClientPrivileges(0)
        if self.privileges & Privileges.UNRESTRICTED:
            to_return |= ClientPrivileges.PLAYER
        if self.privileges & Privileges.DONATOR:
            to_return |= ClientPrivileges.SUPPORTER
        if self.privileges & Privileges.MODERATOR:
            to_return |= ClientPrivileges.MODERATOR
        if self.privileges & Privileges.ADMINISTRATOR:
            to_return |= ClientPrivileges.DEVELOPER
        if self.privileges & Privileges.OWNER:
            to_return |= ClientPrivileges.OWNER

        return to_return

    @property
    def is_restricted(self) -> bool:
        """Whether the user is restricted or not"""
        return not self.privileges & Privileges.UNRESTRICTED

    @property
    def gamemode_stats(self) -> ModeData:
        return self.stats[self.status.mode]

    @property
    def recent_score(self) -> Score | None:
        """Player's most recent submitted score"""
        score = None
        for s in self.recent_scores.values():
            if not s:
                continue

            if not score:
                score = s

            if s.server_time > score.server_time:
                score = s

        return score

    @staticmethod
    def generate_token() -> str:
        """Generate a random token for communication with the osu! client"""
        return str(uuid.uuid4())

    @staticmethod
    def make_safe_name(name: str) -> str:
        """Return a safe name for usage with sql"""
        return name.lower().replace(" ", "_")

    def logout(self) -> None:
        """Log the user out of the server"""
        self.token = ""
        if self.match:
            self.leave_match()

        if self.spectating:
            self.spectating.remove_spectator(self)

        # TODO: Make it in a more intuitive way maybe?
        while self.channels:
            self.leave_channel(self.channels[0], kick=False)

        Sessions.online_players.remove(self)

        if not self.is_restricted:
            Sessions.online_players.enqueue_packet(Packets.Logout(self.id))

        log(f"{self} logged out", Colors.YELLOW)

    def update_privileges(self, new_privileges: Privileges) -> None:
        """Sets user's `privileges` to `new_privileges`"""
        self.privileges = new_privileges

        # TODO: Update db to have consistent naming
        query = "UPDATE users SET priv = %(privileges)s WHERE id = %(id)s"
        arguments = {"privileges": self.privileges, "id": self.id}
        database.execute(query, arguments)

        if "bancho_privileges" in self.__dict__:
            # Wipe cached bancho privileges
            del self.bancho_privileges

    def add_privileges(self, new_privileges: Privileges) -> None:
        """Add `new_privileges` to user's privileges"""
        self.privileges |= new_privileges

        # TODO: Update db to have consistent naming
        query = "UPDATE users SET priv = %(privileges)s WHERE id = %(id)s"
        arguments = {"privileges": self.privileges, "id": self.id}
        database.execute(query, arguments)

        if "bancho_privileges" in self.__dict__:
            # Wipe cached bancho privileges
            del self.bancho_privileges

        if self.is_online:
            self.enqueue_packet(Packets.BanchoPrivileges(self.bancho_privileges))

    def remove_privileges(self, privileges_to_remove: Privileges) -> None:
        """Remove `privileges_to_remove` from user's privileges"""
        self.privileges &= ~privileges_to_remove

        # TODO: Update db to have consistent naming
        query = "UPDATE users SET priv = %(privileges)s WHERE id = %(id)s"
        arguments = {"privileges": self.privileges, "id": self.id}
        database.execute(query, arguments)

        if "bancho_privileges" in self.__dict__:
            # Wipe cached bancho privileges
            del self.bancho_privileges

        if self.is_online:
            self.enqueue_packet(Packets.BanchoPrivileges(self.bancho_privileges))

    def restrict(self, staff_member: Player, reason: str) -> None:
        """Restrict user for `reason` and log to database"""
        self.remove_privileges(Privileges.UNRESTRICTED)

        query = "INSERT INTO LOGS (from, to, action, msg, time) VALUES (%(from)s, %(to)s, %(msg)s, NOW())"
        arguments = {
            "from": staff_member.id,
            "to": self.id,
            "action": "restrict",
            "msg": reason,
        }
        database.execute(query, arguments)

        # TODO: Remove player from redis rankings
        # for mode in ALLOWED_GAMEMODES:

        log(f"{self} got restricted by {staff_member} for {reason}", Colors.RED)

        # TODO: Send webhook/push notification?

        if self.is_online:
            self.logout()
