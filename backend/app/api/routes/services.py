from uuid import UUID

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import SessionDep
from app.models import (
    Service,
    ServiceCreate,
    ServicePublic,
    ServicesPublic,
    ServiceUpdate,
)

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/", response_model=ServicesPublic)
def read_services(session: SessionDep) -> ServicesPublic:
    """
    Retrieve services.
    """
    services = crud.get_all_services(session=session)
    count = len(services)
    return ServicesPublic(data=services, count=count)


@router.get("/{id}", response_model=ServicePublic)
def read_service(session: SessionDep, id: UUID) -> Service:
    """
    Get service by ID.
    """
    service = crud.get_service_by_id(session=session, service_id=id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.post("/", response_model=ServicePublic)
def create_service_endpoint(
    *, session: SessionDep, service_in: ServiceCreate
) -> Service:
    """
    Create new service.
    """
    service = crud.create_service(session=session, service_in=service_in)
    return service


@router.put("/{id}", response_model=ServicePublic)
def update_service(
    *,
    session: SessionDep,
    id: UUID,
    service_in: ServiceUpdate,
) -> Service:
    """
    Update a service.
    """
    service = crud.get_service_by_id(session=session, service_id=id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    update_dict = service_in.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(service, key, value)

    session.add(service)
    session.commit()
    session.refresh(service)
    return service


@router.delete("/{id}")
def delete_service_endpoint(session: SessionDep, id: UUID) -> dict[str, str]:
    """
    Delete a service.
    """
    service = crud.delete_service(session=session, service_id=id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Service deleted successfully"}
