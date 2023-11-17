from __future__ import annotations
from typing import Iterator, Sequence
from app.constants.privileges import Privileges
from app.logging import log

from app.objects.player import Player
from app.settings import DEBUG


class Players(list[Player]):
    """Currently online players"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def __iter__(self) -> Iterator[Player]:
        return super().__iter__()

    def __contains__(self, player: object) -> bool:
        if isinstance(player, str):
            return player in (player.name for player in self)
        else:
            return super().__contains__(player)

    def __repr__(self) -> str:
        return f'[{", ".join(map(repr, self))}]'

    @property
    def ids(self) -> set[int]:
        """Return a set of ID's of currently logged in players"""
        return {p.id for p in self}

    @property
    def staff(self) -> set[Player]:
        """Return a set of staff that is currently online"""
        return {player for player in self if player.privileges & Privileges.STAFF}

    @property
    def restricted_players(self) -> set[Player]:
        """Return a set of currently logged in restricted players"""
        return {
            player for player in self if not player.privileges & Privileges.UNRESTRICTED
        }

    @property
    def unrestricted_players(self) -> set[Player]:
        """Return a set of currently logged in unrestricted players"""
        return {
            player for player in self if player.privileges & Privileges.UNRESTRICTED
        }

    def enqueue_packet(
        self, data: bytes, immune_to_packet: Sequence[Player] = []
    ) -> None:
        """Enqueue `data` in a packet to all players, except for those that are in `immune_to_packet`"""
        for player in self:
            if player not in immune_to_packet:
                player.enqueue_packet(data)

    def get(
        self, token: str | None = None, id: int | None = None, name: str | None = None
    ):
        """Get a player by `token`, `id`, or `name` from cache"""
        for player in self:
            if token is not None:
                if player.token == token:
                    return player
            elif id is not None:
                if player.id == id:
                    return player
            elif name is not None:
                if player.safe_name == player.make_safe_name(name):
                    return player

        return None

    def append(self, player: Player) -> None:
        """Append `player` to the list"""
        if player in self:
            if DEBUG:
                log(f"{player} double-added to global player list?")
            return

        super().append(player)

    def remove(self, player: Player) -> None:
        """Remove `player` from the list"""
        if player not in self:
            if DEBUG:
                log(f"{player} removed from player list when not online")
            return

        super().remove(player)
