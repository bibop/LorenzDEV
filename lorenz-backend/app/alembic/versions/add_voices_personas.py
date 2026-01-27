"""add voices and personas tables

Revision ID: add_voices_personas
Revises: [previous_migration]
Create Date: 2026-01-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_voices_personas'
down_revision = None  # TODO: Set to previous migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create voices table
    op.create_table(
        'voices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, index=True),
        sa.Column('description', sa.Text),
        sa.Column('audio_url', sa.Text, nullable=False),
        sa.Column('duration_ms', sa.Integer, nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('is_public', sa.Boolean, default=False),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create personas table
    op.create_table(
        'personas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, index=True),
        sa.Column('description', sa.Text),
        sa.Column('role_prompt', sa.Text, nullable=False),
        sa.Column('voice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('voices.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('is_public', sa.Boolean, default=False),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Add persona_id to conversations table
    op.add_column(
        'conversations',
        sa.Column('persona_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('personas.id'))
    )
    
    # Create indexes
    op.create_index('idx_voices_tenant', 'voices', ['tenant_id'])
    op.create_index('idx_voices_creator', 'voices', ['created_by'])
    op.create_index('idx_personas_tenant', 'personas', ['tenant_id'])
    op.create_index('idx_personas_creator', 'personas', ['created_by'])
    op.create_index('idx_personas_voice', 'personas', ['voice_id'])


def downgrade() -> None:
    # Remove persona_id from conversations
    op.drop_column('conversations', 'persona_id')
    
    # Drop indexes
    op.drop_index('idx_personas_voice')
    op.drop_index('idx_personas_creator')
    op.drop_index('idx_personas_tenant')
    op.drop_index('idx_voices_creator')
    op.drop_index('idx_voices_tenant')
    
    # Drop tables
    op.drop_table('personas')
    op.drop_table('voices')
