from fastapi import APIRouter

from app.api.routes import (
    appointments,
    categories,
    clients,
    events,
    items,
    login,
    posts,
    private,
    projects,
    providers,
    services,
    users,
    utils,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(clients.router)
api_router.include_router(appointments.router)
api_router.include_router(providers.router)
api_router.include_router(services.router)
api_router.include_router(categories.router)
api_router.include_router(events.router)
api_router.include_router(posts.router)
api_router.include_router(projects.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
