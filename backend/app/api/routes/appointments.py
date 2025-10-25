from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app import crud
from app.api.deps import SessionDep, get_current_active_superuser
from app.models import Appointment, AppointmentCreate, AppointmentUpdate

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Appointment,
)
def create_appointment(
    *,
    session: SessionDep,
    appointment_in: AppointmentCreate,
) -> Any:
    """
    Create a new appointment.
    """
    db_client = crud.get_client_by_id(
        session=session, client_id=appointment_in.client_id
    )
    if not db_client:
        raise HTTPException(
            status_code=404,
            detail=f"Client with id={appointment_in.client_id} does not exist",
        )

    db_provider = crud.get_provider_by_id(
        session=session, provider_id=appointment_in.provider_id
    )
    if not db_provider:
        raise HTTPException(
            status_code=404,
            detail=f"Provider with id={appointment_in.provider_id} does not exist",
        )

    db_service = crud.get_service_by_id(
        session=session, service_id=appointment_in.service_id
    )
    if not db_service:
        raise HTTPException(
            status_code=404,
            detail=f"Service with id={appointment_in.service_id} does not exist",
        )

    existing_appointment = crud.get_appointment_by_date_and_provider(
        session=session,
        appointment_date=appointment_in.appointment_date,
        provider_id=appointment_in.provider_id,
    )
    if existing_appointment:
        raise HTTPException(
            status_code=400,
            detail="An appointment already exists at this time with the selected provider.",
        )

    appointment = crud.create_appointment(
        session=session, appointment_in=appointment_in
    )
    return appointment


@router.put(
    "/{appointment_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Appointment,
)
def update_appointment(
    *,
    session: SessionDep,
    appointment_id: UUID,
    appointment_in: AppointmentUpdate,
) -> Any:
    """
    Update an existing appointment.
    """
    appointment = crud.get_appointment_by_id(
        session=session, appointment_id=appointment_id
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    updated_appointment = crud.update_appointment(
        session=session, appointment_id=appointment_id, appointment_in=appointment_in
    )

    return updated_appointment


@router.get(
    "/{appointment_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Appointment,
)
def get_appointment(
    *,
    session: SessionDep,
    appointment_id: UUID,
) -> Any:
    """
    Get a specific appointment by appointment_id.
    """
    appointment = crud.get_appointment_by_id(
        session=session, appointment_id=appointment_id
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return appointment


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[Appointment],
)
def get_all_appointments(
    *,
    session: SessionDep,
) -> Any:
    """
    Get all appointments.
    """
    appointments = crud.get_all_appointments(session=session)
    if not appointments:
        raise HTTPException(status_code=404, detail="No appointments found")

    return appointments


@router.delete(
    "/{appointment_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Appointment,
)
def delete_appointment(
    *,
    session: SessionDep,
    appointment_id: UUID,
) -> Any:
    """
    Delete an appointment by appointment_id.
    """
    appointment = crud.get_appointment_by_id(
        session=session, appointment_id=appointment_id
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    crud.delete_appointment(session=session, appointment_id=appointment_id)
    return appointment
