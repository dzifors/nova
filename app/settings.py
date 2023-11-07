from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

def read_bool(value: str) -> bool:
    return value.lower() in ("true", "1", "yes")

MYSQL_HOST = os.environ["MYSQL_HOST"]
MYSQL_PORT = int(os.environ["MYSQL_PORT"])
MYSQL_USERNAME = os.environ["MYSQL_USERNAME"]
MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]
MYSQL_DATABASE = os.environ["MYSQL_DATABASE"]

DATA_DIRECTORY = os.environ["DATA_DIRECTORY"]

SERVER_ADDRESS = os.environ["SERVER_ADDRESS"]
SERVER_PORT = int(os.environ["SERVER_PORT"])

DEBUG = read_bool(os.environ["DEBUG"])

DOMAIN = os.environ["DOMAIN"]

VERSION = "0.0.1"

try:
    TIMEZONE = os.environ["TIMEZONE"]
except KeyError:
    TIMEZONE = "GMT"