from __future__ import annotations

import datetime
from enum import IntEnum
from typing import Optional
from zoneinfo import ZoneInfo
import app.settings

class Colors(IntEnum):
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37

    GRAY = 90
    LIGHT_RED = 91
    LIGHT_GREEN = 92
    LIGHT_YELLOW = 93
    LIGHT_BLUE = 94
    LIGHT_MAGENTA = 95
    LIGHT_CYAN = 96
    LIGHT_WHITE = 97

    RESET = 0

    def __repr__(self) -> str:
        return f"\x1b[{self.value}m"
    

TIMEZONE = ZoneInfo(app.settings.TIMEZONE) if app.settings.TIMEZONE is not None else ZoneInfo("GMT")

def get_current_timestamp() -> str:
    format = "%I:%M:%S%p"
    return f"{datetime.datetime.now(tz=TIMEZONE):{format}}"

def print_color(
    msg: str,
    color: Colors,
    end: str = "\n"
) -> None:
    """Print a string, in a specified color"""
    print(f"{color!r}{msg}{Colors.RESET!r}", end=end)

def log(
    msg: str,
    color: Optional[Colors] = None,
    end: str = "\n"
) -> None:
    """
    Print a string, in a specified color, with the current timestamp in front
    """
    current_timestamp = get_current_timestamp()

    if color:
        print(f"{Colors.GRAY!r}[{current_timestamp}] {color!r}{msg}{Colors.RESET!r}", end=end)
    else:
        print(f"{Colors.GRAY!r}[{current_timestamp}] {Colors.RESET!r}{msg}", end=end)


TIME_ORDER_SUFFIXES = ["nsec", "μsec", "msec", "sec"]
def format_time_magnitude(t: int | float) -> str:
    """
    Outputs nearest time unit from the amount of nanoseconds provided
    """
    suffix = TIME_ORDER_SUFFIXES[0]
    for suffix in TIME_ORDER_SUFFIXES:
        if t < 1000:
            break
        t /= 1000
    return f"{t:.2f} {suffix}"