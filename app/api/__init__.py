from __future__ import annotations

from fastapi import APIRouter
from .v1 import apiv1_router

api_router = APIRouter()

api_router.include_router(apiv1_router)

from . import domains
from . import init_api
from . import middleware