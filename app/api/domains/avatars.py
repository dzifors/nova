""" avatars: serving user avatars """
from __future__ import annotations

from fastapi import APIRouter
from fastapi import status
from fastapi.requests import Request
from fastapi.responses import FileResponse

from pathlib import Path
import os

import app.settings
from app.api.common import responses

AVATARS_PATH = Path(app.settings.DATA_DIRECTORY) / "avatars"

router = APIRouter(tags=[f"Avatars (a.{app.settings.DOMAIN})"])

ALLOWED_EXTENSIONS = ["", ".png", ".jpg", ".gif", ".jpeg", ".jfif"]
@router.get(
    path="/{file_path:path}",
    name="Get User Avatar",
    description="Gets avatar of a user with provided id",
    response_class=FileResponse,
)
async def serve_avatar(file_path: str) -> FileResponse:
    if file_path == "/favicon.ico":
        return responses.error(
            message="Not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    for extension in ALLOWED_EXTENSIONS:
        full_path = os.path.join(AVATARS_PATH, f"{file_path}{extension}")
        if os.path.exists(full_path):
            return FileResponse(full_path)

    default_avatar_path = os.path.join(AVATARS_PATH, "default.jpg")
    return FileResponse(default_avatar_path)