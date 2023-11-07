from __future__ import annotations

import aiohttp
import MySQLdb
import MySQLdb.cursors

http_client: aiohttp.ClientSession

database: MySQLdb.Connection
