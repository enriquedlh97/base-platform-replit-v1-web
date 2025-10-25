"""Add triggers for user creation

Revision ID: a1cc016fc7de
Revises: 4e688438f462
Create Date: 2025-07-23 18:30:11.790646

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'a1cc016fc7de'
down_revision = '4e688438f462'
branch_labels = None
depends_on = None


def upgrade():
    # Grant usage on auth schema to current user (needed for cross-schema trigger)
    op.execute("GRANT USAGE ON SCHEMA auth TO CURRENT_USER;")

    # Create function to handle new user creation from auth.users to public.user
    op.execute("""
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER SET search_path = ''
        AS $$
        BEGIN
          INSERT INTO public.user (id, email, is_active, is_superuser, full_name)
          VALUES (
            NEW.id,
            NEW.email,
            true,  -- Set is_active to true by default
            false, -- New users are never superusers by default
            NULL   -- Leave full_name as NULL initially
          );
          RETURN NEW;
        END;
        $$;
    """)

    # Create trigger on auth.users table to create public.user records
    op.execute("""
        CREATE OR REPLACE TRIGGER on_auth_user_created
          AFTER INSERT ON auth.users
          FOR EACH ROW
          EXECUTE PROCEDURE public.handle_new_user();
    """)




def downgrade():
    # Drop triggers first, then functions
    op.execute("DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;")
    op.execute("DROP FUNCTION IF EXISTS public.handle_new_user();")
