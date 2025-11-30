"""add_workspace_profile_fields

Revision ID: 20251130_profile
Revises: 20251103_add_idempotency
Create Date: 2025-11-30

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = "20251130_profile"
down_revision = "20251103_add_idempotency"
branch_labels = None
depends_on = None


def upgrade():
    # Add new profile fields to workspaces table
    op.add_column(
        "workspaces",
        sa.Column("public_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
    )
    op.add_column(
        "workspaces",
        sa.Column("subtitle", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
    )
    op.add_column(
        "workspaces",
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.add_column(
        "workspaces",
        sa.Column("profile_image_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )

    # Backfill public_name from user's full_name
    op.execute("""
        UPDATE workspaces
        SET public_name = (
            SELECT COALESCE(u.full_name, u.name, '')
            FROM "user" u
            WHERE u.id = workspaces.owner_id
        )
        WHERE public_name IS NULL;
    """)


def downgrade():
    # Remove the profile fields
    op.drop_column("workspaces", "profile_image_url")
    op.drop_column("workspaces", "description")
    op.drop_column("workspaces", "subtitle")
    op.drop_column("workspaces", "public_name")
