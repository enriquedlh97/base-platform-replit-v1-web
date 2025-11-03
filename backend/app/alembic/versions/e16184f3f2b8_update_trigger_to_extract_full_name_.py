"""Update trigger to extract name from auth metadata

Revision ID: e16184f3f2b8
Revises: 2aed138eb160
Create Date: 2025-11-02 23:18:22.797183

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'e16184f3f2b8'
down_revision = '2aed138eb160'
branch_labels = None
depends_on = None


def upgrade():
    # Update the trigger function to extract name from Supabase auth metadata
    # Signup form sends full_name in metadata, we store it as name in our database
    op.execute("""
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER SET search_path = ''
        AS $$
        BEGIN
          INSERT INTO public.user (id, email, is_active, is_superuser, name)
          VALUES (
            NEW.id,
            NEW.email,
            true,  -- Set is_active to true by default
            false, -- New users are never superusers by default
            COALESCE(NEW.raw_user_meta_data->>'full_name', NULL)  -- Extract full_name from metadata and store as name
          );
          RETURN NEW;
        END;
        $$;
    """)


def downgrade():
    # Revert to the previous version that sets name to NULL
    op.execute("""
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER SET search_path = ''
        AS $$
        BEGIN
          INSERT INTO public.user (id, email, is_active, is_superuser, name)
          VALUES (
            NEW.id,
            NEW.email,
            true,
            false,
            NULL
          );
          RETURN NEW;
        END;
        $$;
    """)
