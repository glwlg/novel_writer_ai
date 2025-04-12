# backend/app/routers/__init__.py
from .projects import router as projects_router
from .volumes import router as volumes_router
from .chapters import router as chapters_router
from .scenes import router as scenes_router
from .characters import router as characters_router
from .settings import router as settings_router
from .generation import router as generation_router
from .relationships import router as relationships_router

all_routers = [
    volumes_router,
    chapters_router,
    scenes_router,
    projects_router,
    characters_router,
    settings_router,
    generation_router,
    relationships_router,
]