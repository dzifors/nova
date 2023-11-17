from __future__ import annotations

from re import compile as regex

__all__ = "OSU_VERSION"

OSU_VERSION = regex(
    r"^b(?P<date>\d{8})(?:\.(?P<revision>\d))?"
    r"(?P<stream>beta|cuttingedge|dev|tourney)?$",
)
