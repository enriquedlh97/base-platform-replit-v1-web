from fastapi import APIRouter

from app.api.routes import (
    appointments,
    categories,
    clients,
    conversations,
    events,
    items,
    login,
    messages,
    posts,
    private,
    projects,
    providers,
    scheduling_connectors,
    services,
    users,
    utils,
    workspace_services,
    workspaces,
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
# Phase 1: New workspace routes
api_router.include_router(workspaces.router)
api_router.include_router(workspace_services.router)
api_router.include_router(scheduling_connectors.router)
api_router.include_router(conversations.router)
api_router.include_router(messages.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
