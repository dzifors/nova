from __future__ import annotations
from functools import cache, lru_cache
import random
import struct

from typing import TYPE_CHECKING, Any, Callable, Collection, Iterator, NamedTuple, cast
from struct import pack as pack_struct

# from app.objects.match import Match
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum, unique
import struct

if TYPE_CHECKING:
    from app.objects.player import Player

from app.settings import TIMEZONE

SCOREFRAME_FORMAT = struct.Struct("<iBHHHHHHiHH?BB?")


@unique
class ClientPackets(IntEnum):
    CHANGE_ACTION = 0
    SEND_PUBLIC_MESSAGE = 1
    LOGOUT = 2
    REQUEST_STATUS_UPDATE = 3
    PING = 4
    START_SPECTATING = 16
    STOP_SPECTATING = 17
    SPECTATE_FRAMES = 18
    ERROR_REPORT = 20
    CANT_SPECTATE = 21
    SEND_PRIVATE_MESSAGE = 25
    PART_LOBBY = 29
    JOIN_LOBBY = 30
    CREATE_MATCH = 31
    JOIN_MATCH = 32
    PART_MATCH = 33
    MATCH_CHANGE_SLOT = 38
    MATCH_READY = 39
    MATCH_LOCK = 40
    MATCH_CHANGE_SETTINGS = 41
    MATCH_START = 44
    MATCH_SCORE_UPDATE = 47
    MATCH_COMPLETE = 49
    MATCH_CHANGE_MODS = 51
    MATCH_LOAD_COMPLETE = 52
    MATCH_NO_BEATMAP = 54
    MATCH_NOT_READY = 55
    MATCH_FAILED = 56
    MATCH_HAS_BEATMAP = 59
    MATCH_SKIP_REQUEST = 60
    CHANNEL_JOIN = 63
    BEATMAP_INFO_REQUEST = 68
    MATCH_TRANSFER_HOST = 70
    FRIEND_ADD = 73
    FRIEND_REMOVE = 74
    MATCH_CHANGE_TEAM = 77
    CHANNEL_PART = 78
    RECEIVE_UPDATES = 79
    SET_AWAY_MESSAGE = 82
    IRC_ONLY = 84
    USER_STATS_REQUEST = 85
    MATCH_INVITE = 87
    MATCH_CHANGE_PASSWORD = 90
    TOURNAMENT_MATCH_INFO_REQUEST = 93
    USER_PRESENCE_REQUEST = 97
    USER_PRESENCE_REQUEST_ALL = 98
    TOGGLE_BLOCK_NON_FRIEND_DMS = 99
    TOURNAMENT_JOIN_MATCH_CHANNEL = 108
    TOURNAMENT_LEAVE_MATCH_CHANNEL = 109

    def __repr__(self) -> str:
        return f"<{self.name} ({self.value})>"


@unique
class ServerPackets(IntEnum):
    USER_ID = 5
    SEND_MESSAGE = 7
    PONG = 8
    HANDLE_IRC_CHANGE_USERNAME = 9  # unused
    HANDLE_IRC_QUIT = 10
    USER_STATS = 11
    USER_LOGOUT = 12
    SPECTATOR_JOINED = 13
    SPECTATOR_LEFT = 14
    SPECTATE_FRAMES = 15
    VERSION_UPDATE = 19
    SPECTATOR_CANT_SPECTATE = 22
    GET_ATTENTION = 23
    NOTIFICATION = 24
    UPDATE_MATCH = 26
    NEW_MATCH = 27
    DISPOSE_MATCH = 28
    TOGGLE_BLOCK_NON_FRIEND_DMS = 34
    MATCH_JOIN_SUCCESS = 36
    MATCH_JOIN_FAIL = 37
    FELLOW_SPECTATOR_JOINED = 42
    FELLOW_SPECTATOR_LEFT = 43
    ALL_PLAYERS_LOADED = 45
    MATCH_START = 46
    MATCH_SCORE_UPDATE = 48
    MATCH_TRANSFER_HOST = 50
    MATCH_ALL_PLAYERS_LOADED = 53
    MATCH_PLAYER_FAILED = 57
    MATCH_COMPLETE = 58
    MATCH_SKIP = 61
    UNAUTHORIZED = 62  # unused
    CHANNEL_JOIN_SUCCESS = 64
    CHANNEL_INFO = 65
    CHANNEL_KICK = 66
    CHANNEL_AUTO_JOIN = 67
    BEATMAP_INFO_REPLY = 69
    PRIVILEGES = 71
    FRIENDS_LIST = 72
    PROTOCOL_VERSION = 75
    MAIN_MENU_ICON = 76
    MONITOR = 80  # unused
    MATCH_PLAYER_SKIPPED = 81
    USER_PRESENCE = 83
    RESTART = 86
    MATCH_INVITE = 88
    CHANNEL_INFO_END = 89
    MATCH_CHANGE_PASSWORD = 91
    SILENCE_END = 92
    USER_SILENCED = 94
    USER_PRESENCE_SINGLE = 95
    USER_PRESENCE_BUNDLE = 96
    USER_DM_BLOCKED = 100
    TARGET_IS_SILENCED = 101
    VERSION_UPDATE_FORCED = 102
    SWITCH_SERVER = 103
    ACCOUNT_RESTRICTED = 104
    RTX = 105  # unused
    MATCH_ABORT = 106
    SWITCH_TOURNAMENT_SERVER = 107

    def __repr__(self) -> str:
        return f"<{self.name} ({self.value})>"


@unique
class OsuTypes(IntEnum):
    # Integral types
    Int8 = 0
    UnsignedInt8 = 1
    Int16 = 2
    UnsignedInt16 = 3
    Int32 = 4
    UnsignedInt32 = 5
    Float32 = 6
    Int64 = 7
    UnsignedInt64 = 8
    Float64 = 9

    # osu! types
    Message = 11
    Channel = 12
    Match = 13
    ScoreFrame = 14
    MapInfoRequest = 15
    MapInfoReply = 16
    ReplayFrameBundle = 17

    # Miscellaneous types
    Int32List2BytesLength = 18
    Int32List4BytesLength = 19
    String = 20
    Raw = 21


class Message(NamedTuple):
    sender: str
    text: str
    recipient: str
    sender_id: int


class Channel(NamedTuple):
    name: str
    topic: str
    players: int


class ReplayAction(IntEnum):
    Standard = 0
    NewSong = 1
    Skip = 2
    Completion = 3
    Fail = 4
    Pause = 5
    Unpause = 6
    SongSelect = 7
    WatchingOther = 8


@dataclass
class ScoreFrame:
    time: int
    id: int
    count_300: int
    count_100: int
    count_50: int
    count_geki: int
    count_katu: int
    count_miss: int
    total_score: int
    current_combo: int
    max_combo: int
    perfect: bool
    current_hp: int
    tag_byte: int

    score_v2: bool

    # If score_v2 == True
    combo_portion: float | None
    bonus_portion: float | None


class ReplayFrame:
    button_state: int
    taiko_byte: int
    x: float
    y: float
    time: int

    def __init__(
        self, button_state: int, taiko_byte: int, x: float, y: float, time: int
    ) -> None:
        self.button_state = button_state
        self.taiko_byte = taiko_byte
        self.x = x
        self.y = y
        self.time = time


class ReplayFrameBundle:
    replay_frames: list[ReplayFrame]
    score_frame: ScoreFrame
    action: ReplayAction
    extra: int
    sequence: int
    raw_data: memoryview  # This is read-only

    def __init__(
        self,
        replay_frames: list[ReplayFrame],
        score_frame: ScoreFrame,
        action: ReplayAction,
        extra: int,
        sequence: int,
        raw_data: memoryview,
    ) -> None:
        self.replay_frames = replay_frames
        self.score_frame = score_frame
        self.action = action
        self.extra = extra
        self.sequence = sequence
        self.raw_data = raw_data


@dataclass
class MultiplayerMatch:
    id: int = 0
    in_progress: bool = False

    powerplay: int = 0  # OsuTypes.Int8
    mods: int = 0  # OsuTypes.Int32
    name: str = ""
    password: str = ""

    map_name: str = ""
    map_id: int = 0  # OsuTypes.Int32
    map_md5: str = ""

    slot_statuses: list[int] = field(default_factory=list)  # OsuTypes.Int8
    slot_teams: list[int] = field(default_factory=list)  # OsuTypes.Int8
    slot_ids: list[int] = field(default_factory=list)  # OsuTypes.Int8

    host_id: int = 8  # OsuTypes.Int32

    mode: int = 0  # OsuTypes.Int8
    win_condition: int = 0  # OsuTypes.Int8
    team_type: int = 0  # OsuTypes.Int8

    freemod: bool = False  # OsuTypes.Int8
    slot_mods: list[int] = field(default_factory=list)  # OsuTypes.Int32

    seed: int = 0  # OsuTypes.Int32 - used for osu!mania Random mod


class BasePacket(ABC):
    def __init__(self, reader: BanchoPacketReader) -> None:
        ...

    @abstractmethod
    async def handle(self, player: Player) -> None:
        ...


PacketMap = dict[ClientPackets, type[BasePacket]]


class BanchoPacketReader:
    """
    Class for reading bancho packets from the osu! client's request

    Attributes:
    -----------
    body_view: `memoryview`
        A read-only view of the request's body

    packet_map: `dict[ClientPackets, BasePacket]`
        A map of registered packets that the reader can handle

    current_length: `int`
        The length in bytes of the packet currently being handled
    """

    def __init__(self, body_view: memoryview, packet_map: PacketMap) -> None:
        self.body_view = body_view
        self.packet_map = packet_map
        self.current_length = 0

    def __iter__(self) -> Iterator[BasePacket]:
        return self

    def __next__(self) -> BasePacket:
        # Wait to break until we've read the packet's header
        while self.body_view:
            packet_type, packet_length = self._read_header()

            if packet_type not in self.packet_map:
                # Packet type not handled, remove from buffer and continue
                if packet_length != 0:
                    self.body_view = self.body_view[packet_length:]

            else:
                break

        else:
            raise StopIteration

        packet_class = self.packet_map[packet_type]
        self.current_length = packet_length

        return packet_class(self)

    def _read_header(self) -> tuple[ClientPackets, int]:
        """Read the header of an osu! packet"""
        packet_data = struct.unpack("<HxI", self.body_view[:7])
        self.body_view = self.body_view[7:]

        return ClientPackets(packet_data[0]), packet_data[1]

    """ Public API (exposed for packet handler's __init__ methods) """

    def read_raw(self) -> memoryview:
        value = self.body_view[: self.current_length]
        self.body_view = self.body_view[self.current_length :]
        return value

    # Integral types

    def read_int8(self) -> int:
        value = self.body_view[0]
        self.body_view = self.body_view[1:]

        if value > 127:
            return value - 256

        return value

    def read_unsigned_int8(self) -> int:
        value = self.body_view[0]
        self.body_view = self.body_view[1:]

        return value

    def read_int16(self) -> int:
        value = int.from_bytes(self.body_view[:2], "little", signed=True)
        self.body_view = self.body_view[2:]

        return value

    def read_unsigned_int16(self) -> int:
        value = int.from_bytes(self.body_view[:2], "little", signed=False)
        self.body_view = self.body_view[2:]

        return value

    def read_int32(self) -> int:
        value = int.from_bytes(self.body_view[4:], "little", signed=True)
        self.body_view = self.body_view[4:]

        return value

    def read_unsigned_int32(self) -> int:
        value = int.from_bytes(self.body_view[4:], "little", signed=False)
        self.body_view = self.body_view[4:]

        return value

    def read_int64(self) -> int:
        value = int.from_bytes(self.body_view[8:], "little", signed=True)
        self.body_view = self.body_view[8:]

        return value

    def read_unsigned_int64(self) -> int:
        value = int.from_bytes(self.body_view[8:], "little", signed=False)
        self.body_view = self.body_view[8:]

        return value

    # Floating point types

    def read_float16(self) -> float:
        value, _ = struct.unpack_from("<e", self.body_view[:2])
        self.body_view = self.body_view[2:]

        return cast(float, value)

    def read_float32(self) -> float:
        value, _ = struct.unpack_from("<e", self.body_view[:4])
        self.body_view = self.body_view[4:]

        return cast(float, value)

    def read_float64(self) -> float:
        value, _ = struct.unpack_from("<e", self.body_view[:8])
        self.body_view = self.body_view[8:]

        return cast(float, value)

    # Complex types
    # Some osu! packets use OsuTypes.Int16 for array length, while others use OsuTypes.Int32

    def read_int32_list_int16_length(self) -> tuple[int, ...]:
        length = int.from_bytes(self.body_view[:2], "little")
        self.body_view = self.body_view[2:]

        value = struct.unpack(f'<{"I" * length}', self.body_view[: length * 4])
        self.body_view = self.body_view[length * 4 :]

        return value

    def read_int32_list_int32_length(self) -> tuple[int, ...]:
        length = int.from_bytes(self.body_view[:4], "little")
        self.body_view = self.body_view[4:]

        value = struct.unpack(f'<{"I" * length}', self.body_view[: length * 4])
        self.body_view = self.body_view[length * 4 :]

        return value

    def read_string(self) -> str:
        exists = self.body_view[0] == 0x0B
        self.body_view = self.body_view[1:]

        if not exists:
            # No string sent.
            return ""

        # Non-empty string, decode str length (ULEB128)
        length = shift = 0

        while True:
            current_byte = self.body_view[0]
            self.body_view = self.body_view[1:]

            length |= (current_byte & 0x7F) << shift
            if (current_byte & 0x80) == 0:
                break

            shift += 7

        value = self.body_view[:length].tobytes().decode()
        self.body_view = self.body_view[length:]
        return value

    # Custom osu! types

    def read_message(self) -> Message:
        """Read an osu! message from the internal buffer"""
        return Message(
            sender=self.read_string(),
            text=self.read_string(),
            recipient=self.read_string(),
            sender_id=self.read_int32(),
        )

    def read_channel(self) -> Channel:
        """Read an osu! channel from the internal buffer"""
        return Channel(
            name=self.read_string(), topic=self.read_string(), players=self.read_int32()
        )

    def read_match(self) -> MultiplayerMatch:
        """Read an osu! match from the internal buffer"""
        match = MultiplayerMatch(
            id=self.read_int16(),
            in_progress=self.read_int8() == 1,
            powerplay=self.read_int8(),
            mods=self.read_int32(),
            name=self.read_string(),
            password=self.read_string(),
            map_name=self.read_string(),
            map_id=self.read_int32(),
            map_md5=self.read_string(),
            slot_statuses=[self.read_int8() for _ in range(16)],
            slot_teams=[self.read_int8() for _ in range(16)],
            # ^^ up to slot_ids, as it relies on slot_statuses ^^
        )

        for status in match.slot_statuses:
            if status & 124 != 0:
                match.slot_ids.append(self.read_int32())

        match.host_id = self.read_int32()
        match.mode = self.read_int8()
        match.win_condition = self.read_int8()
        match.team_type = self.read_int8()
        match.freemod = self.read_int8() == 1

        if match.freemod:
            match.slot_mods = [self.read_int32() for _ in range(16)]

        match.seed = self.read_int32()  # Used for osu!mania Random mod

        return match

    def read_scoreframe(self) -> ScoreFrame:
        """Read an osu! scoreframe from the internal buffer"""
        score_frame = ScoreFrame(*SCOREFRAME_FORMAT.unpack_from(self.body_view[:29]))
        self.body_view = self.body_view[29:]

        if score_frame.score_v2:
            score_frame.combo_portion = self.read_float64()
            score_frame.bonus_portion = self.read_float64()

        return score_frame

    def read_replayframe(self) -> ReplayFrame:
        return ReplayFrame(
            button_state=self.read_unsigned_int8(),
            taiko_byte=self.read_unsigned_int8(),
            x=self.read_float32(),
            y=self.read_float32(),
            time=self.read_int32(),
        )

    def read_replayframe_bundle(self) -> ReplayFrameBundle:
        raw_data = self.body_view[: self.current_length]

        extra = self.read_int32()
        frame_count = self.read_unsigned_int16()
        frames = [self.read_replayframe() for _ in range(frame_count)]
        action = ReplayAction(self.read_unsigned_int8())
        scoreframe = self.read_scoreframe()
        sequence = self.read_unsigned_int16()

        return ReplayFrameBundle(frames, scoreframe, action, extra, sequence, raw_data)


def write_unsigned_leb128(number: int) -> bytes | bytearray:
    """Write `number` into an unsigned Little Endian Base128"""
    if number == 0:
        return b"\x00"

    to_return = bytearray()

    while number != 0:
        to_return.append(number & 0x7F)
        number >>= 7
        if number != 0:
            to_return[-1] |= 0x80

    return to_return


def write_string(string: str) -> bytes:
    """Write `string` into bytes (Unsigned Little Endian Base128 & string)"""
    if string:
        encoded_string = string.encode()
        to_return = (
            b"\x0b" + write_unsigned_leb128(len(encoded_string)) + encoded_string
        )
    else:
        to_return = b"\x00"

    return to_return


def write_int32_list_2_bytes_length(list: Collection[int]) -> bytearray:
    """Write `list` into bytes (int32 list)"""
    to_return = bytearray(len(list).to_bytes(2, "little"))

    for element in list:
        to_return += element.to_bytes(4, "little", signed=True)

    return to_return


def write_message(
    sender: str, message: str, recipient: str, sender_id: int
) -> bytearray:
    """Write `sender`, `message`, `recipient`, `sender_id` into bytes (osu! message)"""
    sender_bytes = write_string(sender)
    message_bytes = write_string(message)
    recipient_bytes = write_string(recipient)
    sender_id_bytes = sender_id.to_bytes(4, "little", signed=True)
    return bytearray(sender_bytes) + message_bytes + recipient_bytes + sender_id_bytes


def write_channel(name: str, topic: str, count: int) -> bytearray:
    """Write `name`, `topic`, `count` (osu! channel)"""
    name_bytes = write_string(name)
    topic_bytes = write_string(topic)
    count_bytes = count.to_bytes(2, "little")

    return bytearray(name_bytes) + topic_bytes + count_bytes


# TODO: Multiplayer
# def write_match(match: Match, send_password: bool = True) -> bytearray:
#     """Write `match` into bytes (osu! match)"""


def write_scoreframe(score_frame: ScoreFrame) -> bytes:
    """Write `score_frame` into bytes (osu! score frame)"""
    return SCOREFRAME_FORMAT.pack(
        score_frame.time,
        score_frame.id,
        score_frame.count_300,
        score_frame.count_100,
        score_frame.count_50,
        score_frame.count_geki,
        score_frame.count_katu,
        score_frame.count_miss,
        score_frame.total_score,
        score_frame.current_combo,
        score_frame.max_combo,
        score_frame.perfect,
        score_frame.current_hp,
        score_frame.tag_byte,
        score_frame.score_v2,
    )


def write_packet(packet_id: int, *args: tuple[Any, OsuTypes]) -> bytes:
    """Write `args` into an osu! packet"""

    to_return = bytearray(pack_struct("<Hx", packet_id))

    for packet_arguments, packet_type in args:
        if packet_type == OsuTypes.Raw:
            to_return += packet_arguments
        elif packet_type in noexpand_types:
            to_return += noexpand_types[packet_type](packet_arguments)
        elif packet_type in expand_types:
            to_return += expand_types[packet_type](*packet_arguments)

    to_return[3:3] = pack_struct("<I", len(to_return) - 3)
    return bytes(to_return)


noexpand_types: dict[OsuTypes, Callable[..., bytes]] = {
    OsuTypes.Int8: struct.Struct("<b").pack,
    OsuTypes.UnsignedInt8: struct.Struct("<B").pack,
    OsuTypes.Int16: struct.Struct("<h").pack,
    OsuTypes.UnsignedInt16: struct.Struct("<H").pack,
    OsuTypes.Int32: struct.Struct("<i").pack,
    OsuTypes.UnsignedInt32: struct.Struct("<I").pack,
    # OsuTypes.f16: struct.Struct('<e').pack, # futureproofing
    OsuTypes.Float32: struct.Struct("<f").pack,
    OsuTypes.Int64: struct.Struct("<q").pack,
    OsuTypes.UnsignedInt64: struct.Struct("<Q").pack,
    OsuTypes.Float64: struct.Struct("<d").pack,
    # more complex
    OsuTypes.String: write_string,
    OsuTypes.Int32List2BytesLength: write_int32_list_2_bytes_length,
    OsuTypes.ScoreFrame: write_scoreframe,
}

expand_types: dict[OsuTypes, Callable[..., bytearray]] = {
    OsuTypes.Message: write_message,
    OsuTypes.Channel: write_channel,
    # OsuTypes.Match: write_match,
}

# Packets


# Packet id: 5
@cache
def UserId(response: int) -> bytes:
    """
    Write the packet 5 (user id)

    Responses
    ---------
    `-1` - Authentication failed\n
    `-2` - Old client\n
    `-3` - Banned\n
    `-4` - Banned\n
    `-5` - Error Occurred\n
    `-6` - Needs Supporter\n
    `-7` - Password Reset\n
    `-8` - Requires Verification\n
    Anything else - valid id
    """
    return write_packet(ServerPackets.USER_ID, (response, OsuTypes.Int32))


# Packet id: 7
def SendMessage(sender: str, message: str, recipient: str, sender_id: int) -> bytes:
    return write_packet(
        ServerPackets.SEND_MESSAGE,
        ((sender, message, recipient, sender_id), OsuTypes.Message),
    )


# Packet id: 8
@cache
def Pong() -> bytes:
    return write_packet(ServerPackets.PONG)


ACTION_WATCHING = 6

BOT_STATUSES = (
    (ACTION_WATCHING, "over your shoulder"),
    (ACTION_WATCHING, "the inside of your walls"),
    (ACTION_WATCHING, "you sleep :3"),
)


@cache
def bot_stats(player: Player) -> bytes:
    status_id, status_text = random.choice(BOT_STATUSES)

    return write_packet(
        ServerPackets.USER_STATS,
        (player.id, OsuTypes.Int32),
        (status_id, OsuTypes.UnsignedInt8),  # Action
        (status_text, OsuTypes.String),  # Action info text
        ("", OsuTypes.String),  # Map md5
        (0, OsuTypes.Int32),  # Mods
        (0, OsuTypes.UnsignedInt8),  # Mode
        (0, OsuTypes.Int32),  # Map ID
        (0, OsuTypes.Int64),  # Ranked score
        (100.0, OsuTypes.Float32),  # Accuracy
        (0, OsuTypes.Int32),  # Playcount
        (0, OsuTypes.Int64),  # Total score
        (0, OsuTypes.Int32),  # Rank
        (2137, OsuTypes.Int16),  # pp
    )


# Packet id: 11
def UserStats(player: Player) -> bytes:
    INGAME_PP_LIMIT = 0x7FFF
    gamemode_stats = player.gamemode_stats

    if gamemode_stats.pp > INGAME_PP_LIMIT:
        ranked_score = gamemode_stats.pp
        pp = 0
    else:
        ranked_score = gamemode_stats.ranked_score
        pp = gamemode_stats.pp

    id = player.id
    action = player.status.action
    action_info = player.status.action_info
    map_md5 = player.status.map_md5
    mods = player.status.mods
    mode = player.status.mode.as_vanilla
    map_id = player.status.map_id

    acc = gamemode_stats.acc / 100.0
    playcount = gamemode_stats.playcount
    total_score = gamemode_stats.total_score
    rank = gamemode_stats.rank

    return write_packet(
        ServerPackets.USER_STATS,
        (id, OsuTypes.Int32),
        (action, OsuTypes.UnsignedInt8),
        (action_info, OsuTypes.String),
        (map_md5, OsuTypes.String),
        (mods, OsuTypes.Int32),
        (mode, OsuTypes.UnsignedInt8),
        (map_id, OsuTypes.Int32),
        (ranked_score, OsuTypes.Int64),
        (acc, OsuTypes.Float32),
        (playcount, OsuTypes.Float32),
        (total_score, OsuTypes.Int64),
        (rank, OsuTypes.Int32),
        (pp, OsuTypes.Int16),
    )


# Packet id: 12
@cache
def Logout(user_id: int) -> bytes:
    return write_packet(
        ServerPackets.USER_LOGOUT, (user_id, OsuTypes.Int32), (0, OsuTypes.UnsignedInt8)
    )


# Packet id: 13
@cache
def SpectatorJoined(user_id: int) -> bytes:
    return write_packet(ServerPackets.SPECTATOR_JOINED, (user_id, OsuTypes.Int32))


# Packet id: 14
@cache
def SpectatorLeft(user_id: int) -> bytes:
    return write_packet(ServerPackets.SPECTATOR_LEFT, (user_id, OsuTypes.Int32))


# Packet id: 16
def SpectateFrames(data: bytes) -> bytes:
    return write_packet(ServerPackets.SPECTATE_FRAMES, (data, OsuTypes.Raw))


# Packet id: 19
@cache
def VersionUpdate() -> bytes:
    return write_packet(ServerPackets.VERSION_UPDATE)


# Packet id: 22
def SpectatorCantSpectate(user_id: int) -> bytes:
    return write_packet(
        ServerPackets.SPECTATOR_CANT_SPECTATE, (user_id, OsuTypes.Int32)
    )


# Packet id: 23
def GetAttention() -> bytes:
    return write_packet(ServerPackets.GET_ATTENTION)


# Packet id: 24
@lru_cache(maxsize=4)
def Notification(message: str) -> bytes:
    return write_packet(ServerPackets.NOTIFICATION, (message, OsuTypes.String))


# TODO: Multiplayer
# Packet id: 26
# def UpdateMatch(match: Match, send_password: bool = True) -> bytes:
#     return write_packet(ServerPackets.UPDATE_MATCH, ((match, send_password), OsuTypes.Match))

# TODO: Multiplayer
# Packet id: 27
# def NewMatch(match: Match) -> bytes:
#     return write_packet(ServerPackets.NEW_MATCH, ((match, True), OsuTypes.Match))


# Packet id: 28
@cache
def DisposeMatch(id: int) -> bytes:
    return write_packet(ServerPackets.DISPOSE_MATCH, (id, OsuTypes.Int32))


# Packet id: 34
def ToggleBlockNonFriendDMs() -> bytes:
    return write_packet(ServerPackets.TOGGLE_BLOCK_NON_FRIEND_DMS)


# TODO: Multiplayer
# Packet id: 36
# def MatchJoinSuccess(match: Match):
#     return write_packet(ServerPackets.MATCH_JOIN_SUCCESS, ((match, True), OsuTypes.Match))

# TODO: Multiplayer
# Packet id: 37
# def MatchJoinFailed(match: Match):
#     return write_packet(ServerPackets.MATCH_JOIN_FAIL)


# Packet id: 42
@cache
def FellowSpectatorJoined(user_id: int) -> bytes:
    return write_packet(
        ServerPackets.FELLOW_SPECTATOR_JOINED, (user_id, OsuTypes.Int32)
    )


# Packet id: 43
def FellowSpectatorLeft(user_id: int) -> bytes:
    return write_packet(ServerPackets.FELLOW_SPECTATOR_LEFT, (user_id, OsuTypes.Int32))


# TODO: Multiplayer
# Packet id: 46
# def MatchStart(match: Match) -> bytes:
#     return write_packet(ServerPackets.MATCH_START, ((match, True), OsuTypes.Match))


# Packet id: 48
def MatchScoreUpdate(frame: ScoreFrame) -> bytes:
    return write_packet(ServerPackets.MATCH_SCORE_UPDATE, (frame, OsuTypes.ScoreFrame))


# Packet id: 50
@cache
def MatchTransferHost() -> bytes:
    return write_packet(ServerPackets.MATCH_TRANSFER_HOST)


# Packet id: 53
@cache
def MatchAllPlayersLoaded() -> bytes:
    return write_packet(ServerPackets.MATCH_ALL_PLAYERS_LOADED)


# Packet id: 57
@cache
def MatchPlayerFailed(slot_id: int) -> bytes:
    return write_packet(ServerPackets.MATCH_PLAYER_FAILED, (slot_id, OsuTypes.Int32))


# Packet id: 58
@cache
def MatchComplete() -> bytes:
    return write_packet(ServerPackets.MATCH_COMPLETE)


# Packet id: 61
@cache
def MatchSkip() -> bytes:
    return write_packet(ServerPackets.MATCH_SKIP)


# Packet id: 64
@lru_cache(maxsize=16)
def ChannelJoin(name: str) -> bytes:
    return write_packet(ServerPackets.CHANNEL_JOIN_SUCCESS, (name, OsuTypes.String))


# Packet id: 65
@lru_cache(maxsize=8)
def ChannelInfo(name: str, topic: str, player_count: int) -> bytes:
    return write_packet(
        ServerPackets.CHANNEL_INFO, ((name, topic, player_count), OsuTypes.Channel)
    )


# Packet id: 66
@lru_cache(maxsize=8)
def ChannelKick(name: str) -> bytes:
    return write_packet(ServerPackets.CHANNEL_KICK, (name, OsuTypes.String))


# Packet id: 67
@lru_cache(maxsize=8)
def ChannelAutoJoin(name: str, topic: str, player_count: int) -> bytes:
    return write_packet(
        ServerPackets.CHANNEL_AUTO_JOIN, ((name, topic, player_count), OsuTypes.Channel)
    )


# Packet id: 71
@cache
def BanchoPrivileges(privileges: int) -> bytes:
    return write_packet(ServerPackets.PRIVILEGES, (privileges, OsuTypes.Int32))


# Packet id: 72
def FriendsList(friends: Collection[int]) -> bytes:
    return write_packet(
        ServerPackets.FRIENDS_LIST, (friends, OsuTypes.Int32List2BytesLength)
    )


# Packet id: 75
@cache
def ProtocolVersion(version: int) -> bytes:
    return write_packet(ServerPackets.PROTOCOL_VERSION, (version, OsuTypes.Int32))


# Packet id: 76
@cache
def MainMenuIcon(icon_url: str, onclick_url: str) -> bytes:
    return write_packet(
        ServerPackets.MAIN_MENU_ICON, (f"{icon_url}|{onclick_url}", OsuTypes.String)
    )


# Packet id: 81
@cache
def MatchPlayerSkipped(user_id: int) -> bytes:
    return write_packet(ServerPackets.MATCH_PLAYER_SKIPPED, (user_id, OsuTypes.Int32))


# Packet id: 83
def UserPresence(player: Player) -> bytes:
    return write_packet(
        ServerPackets.USER_PRESENCE,
        (player.id, OsuTypes.Int32),
        (player.name, OsuTypes.String),
        (player.utc_offset + 24, OsuTypes.UnsignedInt8),
        (player.geolocation["country"]["numeric"], OsuTypes.UnsignedInt8),
        (
            player.bancho_privileges | (player.status.mode.as_vanilla << 5),
            OsuTypes.UnsignedInt8,
        ),
        (player.geolocation["longitude"], OsuTypes.Float32),
        (player.geolocation["latitude"], OsuTypes.Float32),
        (player.gamemode_stats.rank, OsuTypes.Int32),
    )


@cache
def BotPresence(player: Player) -> bytes:
    return write_packet(
        ServerPackets.USER_PRESENCE,
        (player.id, OsuTypes.Int32),
        (player.name, OsuTypes.String),
        (int(TIMEZONE[4::]) + 24, OsuTypes.UnsignedInt8),
        (245, OsuTypes.UnsignedInt8),  # Satellite Provider
        (31, OsuTypes.UnsignedInt8),
        (1234.0, OsuTypes.Float32),  # Coordinates out
        (4321.0, OsuTypes.Float32),  # of the map
        (0, OsuTypes.Int32),
    )


# Packet id: 86
@cache
def ServerRestarted(ms: int) -> bytes:
    return write_packet(ServerPackets.RESTART, (ms, OsuTypes.Int32))


# Packet id: 88
def MatchInvite(player: Player, target_name: str) -> bytes:
    assert player.match is not None
    message = f"Come join my game: {player.match.embed}"

    return write_packet(
        ServerPackets.MATCH_INVITE,
        ((player.name, message, target_name, player.id), OsuTypes.Message),
    )


# Packet id: 89
@cache
def ChannelInfoEnd() -> bytes:
    return write_packet(ServerPackets.CHANNEL_INFO_END)


# Packet id: 91
def MatchChangePassword(new_password: str) -> bytes:
    return write_packet(
        ServerPackets.MATCH_CHANGE_PASSWORD, (new_password, OsuTypes.String)
    )


# Packet id: 92
def SilenceEnd(delta: int) -> bytes:
    return write_packet(ServerPackets.SILENCE_END, (delta, OsuTypes.Int32))


# Packet id: 94
@cache
def UserSilenced(user_id: int) -> bytes:
    return write_packet(ServerPackets.USER_SILENCED, (user_id, OsuTypes.Int32))


# Packet id: 100
def UserDMBlocked(target: str) -> bytes:
    return write_packet(
        ServerPackets.USER_DM_BLOCKED, (("", "", target, 0), OsuTypes.Message)
    )


# Packet id: 101
def TargetSilenced(target: str) -> bytes:
    return write_packet(ServerPackets.TARGET_IS_SILENCED, (target, OsuTypes.String))


# Packet id: 102
@cache
def VersionUpdateForced() -> bytes:
    return write_packet(ServerPackets.VERSION_UPDATE_FORCED)


# Packet id: 103
def SwitchServer(timeout: int) -> bytes:
    return write_packet(ServerPackets.SWITCH_SERVER, (timeout, OsuTypes.Int32))


# Packet id: 104
@cache
def AccountRestricted() -> bytes:
    return write_packet(ServerPackets.ACCOUNT_RESTRICTED)


# Packet id: 106
@cache
def MatchAbort() -> bytes:
    return write_packet(ServerPackets.MATCH_ABORT)


# Packet id: 107
def SwitchTournamentServer(ip: str) -> bytes:
    return write_packet(ServerPackets.SWITCH_TOURNAMENT_SERVER, (ip, OsuTypes.String))
