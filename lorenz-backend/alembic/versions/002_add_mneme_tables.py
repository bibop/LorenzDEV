"""Add MNEME Knowledge Base tables

Revision ID: 001_mneme_tables
Revises:
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_mneme_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create MNEME knowledge base tables"""

    # Knowledge Entries table
    op.create_table(
        'knowledge_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('context', postgresql.JSON(), default={}),
        sa.Column('access_count', sa.Integer(), default=0),
        sa.Column('confidence', sa.Float(), default=1.0),
        sa.Column('source', sa.String(100), default=''),
        sa.Column('tags', postgresql.JSON(), default=[]),
        sa.Column('related_skills', postgresql.JSON(), default=[]),
        sa.Column('embedding_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_knowledge_entries_user_id', 'knowledge_entries', ['user_id'])
    op.create_index('ix_knowledge_entries_category', 'knowledge_entries', ['category'])

    # Emergent Skills table
    op.create_table(
        'emergent_skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('description_it', sa.Text()),
        sa.Column('trigger_patterns', postgresql.JSON(), default=[]),
        sa.Column('workflow_steps', postgresql.JSON(), default=[]),
        sa.Column('category', sa.String(50), default='custom'),
        sa.Column('use_count', sa.Integer(), default=0),
        sa.Column('success_rate', sa.Float(), default=1.0),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('tags', postgresql.JSON(), default=[]),
        sa.Column('created_from', sa.String(255), default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_emergent_skills_user_id', 'emergent_skills', ['user_id'])

    # Learning History table
    op.create_table(
        'learning_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('skill_name', sa.String(100), nullable=True),
        sa.Column('input_text', sa.Text()),
        sa.Column('result_success', sa.Boolean(), default=True),
        sa.Column('learned_pattern', sa.Text()),
        sa.Column('context', postgresql.JSON(), default={}),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_learning_history_user_id', 'learning_history', ['user_id'])

    # Enable Row-Level Security
    op.execute("""
        ALTER TABLE knowledge_entries ENABLE ROW LEVEL SECURITY;
        ALTER TABLE emergent_skills ENABLE ROW LEVEL SECURITY;
        ALTER TABLE learning_history ENABLE ROW LEVEL SECURITY;
    """)

    # Create RLS policies
    op.execute("""
        CREATE POLICY knowledge_entries_isolation ON knowledge_entries
            USING (user_id = current_setting('app.current_user_id', true)::uuid);

        CREATE POLICY emergent_skills_isolation ON emergent_skills
            USING (user_id = current_setting('app.current_user_id', true)::uuid);

        CREATE POLICY learning_history_isolation ON learning_history
            USING (user_id = current_setting('app.current_user_id', true)::uuid);
    """)


def downgrade() -> None:
    """Drop MNEME tables"""

    # Drop RLS policies
    op.execute("""
        DROP POLICY IF EXISTS knowledge_entries_isolation ON knowledge_entries;
        DROP POLICY IF EXISTS emergent_skills_isolation ON emergent_skills;
        DROP POLICY IF EXISTS learning_history_isolation ON learning_history;
    """)

    # Drop tables
    op.drop_table('learning_history')
    op.drop_table('emergent_skills')
    op.drop_table('knowledge_entries')
