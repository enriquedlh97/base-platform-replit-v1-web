from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app import crud
from app.api.deps import SessionDep, get_current_active_superuser
from app.models import Client, ClientCreate, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Client,
)
def create_client(
    *,
    session: SessionDep,
    client_in: ClientCreate,
) -> Any:
    """
    Create new client.
    """
    client = crud.get_client_by_email(session=session, email=client_in.email)
    if client:
        raise HTTPException(
            status_code=400,
            detail="The client with this email already exists in the system.",
        )
    client = crud.create_client(session=session, client_in=client_in)
    return client


@router.put(
    "/{client_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Client,
)
def update_client(
    *,
    session: SessionDep,
    client_id: UUID,
    client_in: ClientUpdate,
) -> Any:
    """
    Update an existing client.
    """
    client = crud.get_client_by_id(session=session, client_id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    updated_client = crud.update_client(
        session=session, client_id=client_id, client_in=client_in
    )

    return updated_client


@router.get(
    "/{client_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Client,
)
def get_client(
    *,
    session: SessionDep,
    client_id: UUID,
) -> Any:
    """
    Get a specific client by client_id.
    """
    client = crud.get_client_by_id(session=session, client_id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return client


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[Client],
)
def get_all_clients(
    *,
    session: SessionDep,
) -> Any:
    """
    Get all clients.
    """
    clients = crud.get_all_clients(session=session)
    if not clients:
        raise HTTPException(status_code=404, detail="No clients found")

    return clients


@router.delete(
    "/{client_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Client,
)
def delete_client(
    *,
    session: SessionDep,
    client_id: UUID,
) -> Any:
    """
    Delete a client by client_id.
    """
    client = crud.get_client_by_id(session=session, client_id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    crud.delete_client(session=session, client_id=client_id)
    return client
