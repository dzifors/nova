from __future__ import annotations

import io
import ipaddress
import sys
import socket

from typing import Any
from typing import Callable
from typing import Mapping
from typing import Optional
from typing import TypeVar
import types

from app.logging import Colors
from app.logging import log
from app.logging import print_color
import app.settings
from app.types import IPAddress


def _install_synchronous_excepthook() -> None:
    """Install a thin wrapper for sys.excepthook to catch bancho-related stuff."""
    real_excepthook = sys.excepthook  # backup

    def _excepthook(
        type_: type[BaseException],
        value: BaseException,
        traceback: Optional[types.TracebackType],
    ):
        if type_ is KeyboardInterrupt:
            print("\33[2K\r", end="Aborted startup.")
            return
        elif type_ is AttributeError and value.args[0].startswith(
            "module 'config' has no attribute",
        ):
            attr_name = value.args[0][34:-1]
            log(
                "bancho.py's config has been updated, and has "
                f"added a new `{attr_name}` attribute.",
                Colors.MAGENTA,
            )
            log(
                "Please refer to it's value & example in "
                "ext/config.sample.py for additional info.",
                Colors.CYAN,
            )
            return

        print_color(
            f"bancho.py v{app.settings.VERSION} ran into an issue before starting up :(",
            Colors.RED,
        )
        real_excepthook(type_, value, traceback)  # type: ignore

    sys.excepthook = _excepthook


def setup_runtime_environment() -> None:
    # install a hook to catch exceptions outside the event loop,
    # which will handle various situations where the error details
    # can be cleared up for the developer; for example it will explain
    # that the config has been updated when an unknown attribute is
    # accessed, so the developer knows what to do immediately.
    _install_synchronous_excepthook()

    # we print utf-8 content quite often, so configure sys.stdout
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")


def ensure_connected_services(timeout: float = 1.0) -> int:
    """Ensure service connections are functional and running"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((app.settings.MYSQL_HOST, app.settings.MYSQL_PORT))
            log("Connected to MySQL", Colors.GREEN)
        except OSError:
            log("Unable to connect to MySQL server.", Colors.RED)
            return 1

    return 0


# def escape_enum(
#     val: Any,
#     _: Optional[dict[object, object]] = None,
# ) -> str:  # used for ^
#     return str(int(val))


T = TypeVar("T")


# def pymysql_encode(
#     conv: Callable[[Any, Optional[dict[object, object]]], str],
# ) -> Callable[[T], T]:
#     """Decorator to allow for adding to pymysql's encoders."""

#     def wrapper(cls: T) -> T:
#         pymysql.converters.encoders[cls] = conv
#         return cls

#     return wrapper


def get_ip_from_headers(headers: Mapping[str, str]) -> IPAddress:
    ip_from_cloudflare = headers.get("CF-Connecting-IP")
    if ip_from_cloudflare is None:
        forwards = headers["X-Forwarded-For"].split(",")

        if len(forwards) != 1:
            ip_string = forwards[0]
        else:
            ip_string = headers["X-Real-IP"]

    else:
        ip_string = ip_from_cloudflare

    ip = ipaddress.ip_address(ip_string)

    return ip
