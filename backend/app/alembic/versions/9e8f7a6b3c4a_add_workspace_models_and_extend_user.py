"""Add workspace models and extend user profile

Revision ID: 9e8f7a6b3c4a
Revises: 51e2fc18055f
Create Date: 2025-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '9e8f7a6b3c4a'
down_revision = 'da348b6414a5'
branch_labels = None
depends_on = None


def upgrade():
    # Add business profile fields to user table
    op.add_column('user', sa.Column('business_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    op.add_column('user', sa.Column('tagline', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))
    op.add_column('user', sa.Column('bio', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('user', sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True))
    op.add_column('user', sa.Column('website', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))
    op.add_column('user', sa.Column('social_links', sa.JSON(), nullable=True))
    op.add_column('user', sa.Column('setup_completed', sa.Boolean(), nullable=False, server_default='false'))

    # Create workspaces table
    op.create_table('workspaces',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.Column('handle', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('tone', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('timezone', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('owner_id'),
    sa.UniqueConstraint('handle')
    )
    op.create_index(op.f('ix_workspaces_handle'), 'workspaces', ['handle'], unique=True)
    op.create_index(op.f('ix_workspaces_owner_id'), 'workspaces', ['owner_id'], unique=True)

    # Create workspace_services table
    op.create_table('workspace_services',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
    sa.Column('format', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    sa.Column('duration_minutes', sa.Integer(), nullable=True),
    sa.Column('starting_price', sa.Numeric(12, 2), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    # Create scheduling_connectors table
    op.create_table('scheduling_connectors',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('config', sa.JSON(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    # Create conversations table
    op.create_table('conversations',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('visitor_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
    sa.Column('visitor_email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
    sa.Column('channel', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('human_time_saved_minutes', sa.Integer(), nullable=True),
    sa.Column('tags', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    # Create conversation_messages table
    op.create_table('conversation_messages',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('conversation_id', sa.Uuid(), nullable=False),
    sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('role', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop conversation_messages table
    op.drop_table('conversation_messages')

    # Drop conversations table
    op.drop_table('conversations')

    # Drop scheduling_connectors table
    op.drop_table('scheduling_connectors')

    # Drop workspace_services table
    op.drop_table('workspace_services')

    # Drop workspaces table
    op.drop_index(op.f('ix_workspaces_owner_id'), table_name='workspaces')
    op.drop_index(op.f('ix_workspaces_handle'), table_name='workspaces')
    op.drop_table('workspaces')

    # Remove business profile fields from user table
    op.drop_column('user', 'setup_completed')
    op.drop_column('user', 'social_links')
    op.drop_column('user', 'website')
    op.drop_column('user', 'phone')
    op.drop_column('user', 'bio')
    op.drop_column('user', 'tagline')
    op.drop_column('user', 'business_name')
