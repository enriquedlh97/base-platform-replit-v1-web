from typing import Any

from fastapi.testclient import TestClient
from httpx import Response
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from app.tests.utils.utils import random_email


def test_create_user(client: TestClient, db: Session) -> None:
    email: str = random_email()
    response: Response = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json={
            "email": email,
            "full_name": "Pollo Listo",
        },
    )

    assert response.status_code == 200

    data: dict[str, Any] = response.json()

    user: User | None = db.exec(select(User).where(User.id == data["id"])).first()

    assert user
    assert user.email == email
    assert user.full_name == "Pollo Listo"
