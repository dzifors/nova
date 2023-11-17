from __future__ import annotations

import aiohttp
import MySQLdb
import MySQLdb.cursors

import app.settings

http_client: aiohttp.ClientSession

_database_connection: MySQLdb.Connection = MySQLdb.connect(
    host=app.settings.MYSQL_HOST,
    port=app.settings.MYSQL_PORT,
    user=app.settings.MYSQL_USERNAME,
    password=app.settings.MYSQL_PASSWORD,
    database=app.settings.MYSQL_DATABASE,
)

database: MySQLdb.cursors.Cursor = _database_connection.cursor()
