from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.deps import SessionDep
from app.crud import (
    create_provider,
    delete_provider,
    get_all_providers,
    get_provider_by_id,
)
from app.models import (
    Provider,
    ProviderCreate,
    ProviderPublic,
    ProvidersPublic,
    ProviderUpdate,
)

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/", response_model=ProvidersPublic)
def read_providers(session: SessionDep) -> ProvidersPublic:
    """
    Retrieve providers.
    """
    providers = get_all_providers(session=session)
    count = len(providers)
    return ProvidersPublic(data=providers, count=count)


@router.get("/{id}", response_model=ProviderPublic)
def read_provider(session: SessionDep, id: UUID) -> Provider:
    """
    Get provider by ID.
    """
    provider = get_provider_by_id(session=session, provider_id=id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.post("/", response_model=ProviderPublic)
def create_provider_endpoint(
    *, session: SessionDep, provider_in: ProviderCreate
) -> Provider:
    """
    Create new provider.
    """
    provider = create_provider(session=session, provider_in=provider_in)
    return provider


@router.put("/{id}", response_model=ProviderPublic)
def update_provider(
    *,
    session: SessionDep,
    id: UUID,
    provider_in: ProviderUpdate,
) -> Provider:
    """
    Update a provider.
    """
    provider = get_provider_by_id(session=session, provider_id=id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    update_dict = provider_in.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(provider, key, value)

    session.add(provider)
    session.commit()
    session.refresh(provider)
    return provider


@router.delete("/{id}")
def delete_provider_endpoint(session: SessionDep, id: UUID) -> dict[str, str]:
    """
    Delete a provider.
    """
    provider = delete_provider(session=session, provider_id=id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return {"message": "Provider deleted successfully"}
