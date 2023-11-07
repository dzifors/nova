from __future__ import annotations

from fastapi import status
from fastapi.responses import ORJSONResponse

from typing import Any
from typing import Generic
from typing import Literal
from typing import Optional
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    status: Literal["success"]
    data: T
    meta: dict[str, Any]

def success(
    content: Any,
    status_code: int = 200,
    headers: Optional[dict[str, Any]] = None,
    meta: Optional[dict[str, Any]] = None
) -> Any:
    if meta is None:
        meta = {}
    
    data = {
        "status": "success",
        "data": content,
        "meta": meta
    }

    return ORJSONResponse(data, status_code, headers)

class ErrorResponse(BaseModel, Generic[T]):
    status: Literal["error"]
    error: T
    message: str

def error(
    message: str,
    status_code: int,
    headers: dict[str, Any] | None = None
) -> Any:
    data = {
        "status": "error",
        "error": message
    }

    return ORJSONResponse(
        content=data,
        status_code=status_code,
        headers=headers
    )