"""add idempotency_key to conversation_messages

Revision ID: 20251103_add_idempotency
Revises: e16184f3f2b8
Create Date: 2025-11-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251103_add_idempotency"
down_revision: Union[str, None] = "bbf7c4e0e730"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_conversation_messages_idempotency_key",
        "conversation_messages",
        ["idempotency_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_messages_idempotency_key", table_name="conversation_messages")
    op.drop_column("conversation_messages", "idempotency_key")
