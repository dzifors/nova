#!/usr/bin/env python3.11
from __future__ import annotations

__author__ = "Grzegorz Grzegrzółka (dzifors)"
__email__ = "dzifors@nigge.rs"
__discord__ = "dzifors"

import os

# set working directory to the bancho/ directory.
os.chdir(os.path.dirname(os.path.realpath(__file__)))

import argparse

import uvicorn
import logging
import sys

from typing import Sequence

import app.utils
import app.settings


def main(argv: Sequence[str]) -> int:
    """Ensure the runtime environment is ready and start the server"""
    app.utils.setup_runtime_environment()

    # app.utils.ensure_connected_services()

    parser = argparse.ArgumentParser(description="bancho.py but betterer (TM)")

    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s v{app.settings.VERSION}"
    )

    parser.parse_args(argv)

    server_arguments = {
        "host": app.settings.SERVER_ADDRESS,
        "port": app.settings.SERVER_PORT,
    }

    uvicorn.run(
        "app.api.init_api:asgi_app",
        reload=app.settings.DEBUG,
        log_level=logging.WARNING,
        server_header=False,
        date_header=False,
        headers=[("Bancho-Version", app.settings.VERSION)],
        **server_arguments,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
