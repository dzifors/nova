""" players repo: fetch and/or create player accounts """
from __future__ import annotations

import textwrap
from typing import Any
from typing import Optional

import app.state

READ_PARAMS = textwrap.dedent(
    """\
        id, name, safe_name, priv, country, silence_end, donor_end, creation_time,
        latest_activity, clan_id, clan_priv, preferred_mode, play_style, custom_badge_name,
        custom_badge_icon, userpage_content
    """,
)


def make_safe_name(name: str) -> str:
    """Returns a name that is safe for use with MySQL"""
    return name.lower().replace(" ", "_")


def create(
    name: str,
    email: str,
    pw_bcrypt: bytes,
    country: str,
) -> dict[str, Any]:
    """Create a new player in the database."""
    query = f"""\
        INSERT INTO users (name, safe_name, email, pw_bcrypt, country, creation_time, latest_activity)
             VALUES (%(name)s, %(safe_name)s, %(email)s, %(pw_bcrypt)s, %(country)s, UNIX_TIMESTAMP(), UNIX_TIMESTAMP())
    """
    params = {
        "name": name,
        "safe_name": make_safe_name(name),
        "email": email,
        "pw_bcrypt": pw_bcrypt,
        "country": country,
    }
    cursor = app.state.services.database.cursor()

    rec_id = cursor.execute(query, params)
    app.state.services.database.commit()

    query = f"""\
        SELECT {READ_PARAMS}
          FROM users
         WHERE id = %(id)s
    """
    params = {
        "id": rec_id,
    }
    cursor.execute(query, params)
    rec = cursor.fetchone()
    assert rec is not None
    return rec


def get_one(
    id: Optional[int] = None, name: Optional[str] = None, email: Optional[str] = None
):
    if id is None and name is None and email is None:
        raise ValueError("players repo: get_one: Must provide at least one parameter")

    query = f"""
        SELECT {READ_PARAMS}
        FROM users
        WHERE 
    """

    conditions = [
        ("id", id),
        ("safe_name", make_safe_name(name) if name is not None else None),
        ("email", email),
    ]

    query_conditions = []
    params = {}

    for param_name, param_value in conditions:
        if param_value is not None:
            query_conditions.append(f"{param_name} = %({param_name})s")
            params[param_name] = param_value

    if query_conditions:
        query += " AND ".join(query_conditions)

    cursor = app.state.services.database.cursor()

    cursor.execute(query, params)

    result = cursor.fetchone()

    player = (
        {
            "id": result[0],
            "name": result[1],
            "safe_name": result[2],
            "priv": result[3],
            "country": result[4],
            "silence_end": result[5],
            "donor_end": result[6],
            "creation_time": result[7],
            "latest_activity": result[8],
            "clan_id": result[9],
            "clan_priv": result[10],
            "preferred_mode": result[11],
            "play_style": result[12],
            "custom_badge_name": result[13],
            "custom_badge_icon": result[14],
            "userpage_content": result[15],
        }
        if result is not None
        else None
    )

    return player


def count(
    priv: Optional[int] = None,
    country: Optional[str] = None,
    clan_id: Optional[int] = None,
    clan_priv: Optional[int] = None,
    preferred_mode: Optional[int] = None,
    play_style: Optional[int] = None,
) -> int:
    query = (
        f"""
        SELECT COUNT(*) AS count
        FROM users
    """
        if (
            priv is None
            and country is None
            and clan_id is None
            and clan_priv is None
            and preferred_mode is None
            and play_style is None
        )
        else f"""
        SELECT COUNT(*) AS count
        FROM users
        WHERE 
    """
    )

    conditions = [
        # ("id", id),
        # ("safe_name", make_safe_name(name)),
        # ("email", email),
        ("priv", priv),
        ("country", country),
        ("clan_id", clan_id),
        ("clan_priv", clan_priv),
        ("preferred_mode", preferred_mode),
        ("play_style", play_style),
    ]

    query_conditions = []
    params = {}

    for param_name, param_value in conditions:
        if param_value is not None:
            query_conditions.append(f"{param_name} = %({param_name})s")
            params[param_name] = param_value

    if query_conditions:
        query += " AND ".join(query_conditions)

    cursor = app.state.services.database.cursor()
    cursor.execute(query, params)
    count = cursor.fetchone()

    assert count is not None
    return count[0]
