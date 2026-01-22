"""Add Twin tables for Human Digital Twin system

Revision ID: 003_twin_tables
Revises: 001_mneme_tables
Create Date: 2026-01-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers, used by Alembic.
revision: str = '003_twin_tables'
down_revision: Union[str, None] = '001_mneme_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create twin_profiles table
    op.create_table(
        'twin_profiles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), unique=True, nullable=False),

        # Basic Identity
        sa.Column('full_name', sa.String(255)),
        sa.Column('preferred_name', sa.String(100)),
        sa.Column('email_addresses', ARRAY(sa.String), default=[]),
        sa.Column('phone_numbers', ARRAY(sa.String), default=[]),

        # Birth and Astrological Data
        sa.Column('birth_date', sa.Date),
        sa.Column('birth_time', sa.String(10)),
        sa.Column('birth_place', sa.String(255)),
        sa.Column('zodiac_sign', sa.String(50)),
        sa.Column('ascendant', sa.String(50)),
        sa.Column('moon_sign', sa.String(50)),

        # Professional Identity
        sa.Column('current_role', sa.String(255)),
        sa.Column('company', sa.String(255)),
        sa.Column('industry', sa.String(100)),
        sa.Column('professional_titles', ARRAY(sa.String), default=[]),
        sa.Column('expertise_areas', ARRAY(sa.String), default=[]),

        # Personality & Communication
        sa.Column('personality_traits', JSONB, default={}),
        sa.Column('communication_style', sa.String(50), default='direct'),
        sa.Column('languages', ARRAY(sa.String), default=['English']),
        sa.Column('preferred_language', sa.String(50), default='English'),
        sa.Column('tone_preferences', JSONB, default={}),

        # Work Patterns
        sa.Column('work_pattern', JSONB, default={}),

        # Email Preferences
        sa.Column('email_signature_style', sa.String(50), default='professional'),
        sa.Column('auto_archive_categories', ARRAY(sa.String), default=[]),
        sa.Column('priority_senders', ARRAY(sa.String), default=[]),
        sa.Column('response_templates', JSONB, default={}),

        # Calendar Preferences
        sa.Column('meeting_buffer_minutes', sa.Integer, default=15),
        sa.Column('max_meetings_per_day', sa.Integer, default=6),
        sa.Column('preferred_meeting_duration', sa.Integer, default=30),

        # Twin Configuration
        sa.Column('twin_name', sa.String(100), default='LORENZ'),
        sa.Column('twin_personality', sa.String(50), default='professional_proactive'),
        sa.Column('autonomy_level', sa.Integer, default=7),
        sa.Column('notification_preferences', JSONB, default={}),

        # Learning Data
        sa.Column('learned_preferences', JSONB, default={}),
        sa.Column('behavior_patterns', JSONB, default={}),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create twin_contacts table
    op.create_table(
        'twin_contacts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('twin_profile_id', UUID(as_uuid=True), sa.ForeignKey('twin_profiles.id'), nullable=False),

        # Contact Info
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('relationship_type', sa.String(50)),
        sa.Column('importance', sa.Integer, default=5),
        sa.Column('is_vip', sa.Boolean, default=False),

        # Professional Info
        sa.Column('company', sa.String(255)),
        sa.Column('role', sa.String(255)),

        # Interaction Data
        sa.Column('notes', ARRAY(sa.String), default=[]),
        sa.Column('interaction_count', sa.Integer, default=0),
        sa.Column('topics_discussed', ARRAY(sa.String), default=[]),
        sa.Column('sentiment_history', JSONB, default=[]),

        # Communication Preferences
        sa.Column('response_priority', sa.String(20), default='medium'),
        sa.Column('preferred_language', sa.String(50), default='auto'),
        sa.Column('communication_style', sa.String(50)),

        # Research Data
        sa.Column('research_notes', sa.Text),
        sa.Column('linkedin_url', sa.String(500)),
        sa.Column('social_profiles', JSONB, default={}),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create twin_projects table
    op.create_table(
        'twin_projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('twin_profile_id', UUID(as_uuid=True), sa.ForeignKey('twin_profiles.id'), nullable=False),

        # Project Info
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('priority', sa.Integer, default=5),
        sa.Column('status', sa.String(20), default='active'),

        # Related Data
        sa.Column('stakeholders', ARRAY(sa.String), default=[]),
        sa.Column('deadlines', JSONB, default=[]),
        sa.Column('key_topics', ARRAY(sa.String), default=[]),
        sa.Column('related_emails_keywords', ARRAY(sa.String), default=[]),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create twin_learning_events table
    op.create_table(
        'twin_learning_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('twin_profile_id', UUID(as_uuid=True), sa.ForeignKey('twin_profiles.id'), nullable=False),

        # Event Info
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', JSONB, default={}),
        sa.Column('context', JSONB, default={}),

        # Computed Insights
        sa.Column('sentiment', sa.Integer),
        sa.Column('urgency', sa.Integer),
        sa.Column('importance', sa.Integer),

        # Pattern Detection
        sa.Column('patterns_detected', ARRAY(sa.String), default=[]),
        sa.Column('learnings_extracted', JSONB, default={}),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create twin_patterns table
    op.create_table(
        'twin_patterns',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('twin_profile_id', UUID(as_uuid=True), sa.ForeignKey('twin_profiles.id'), nullable=False),

        # Pattern Info
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('pattern_type', sa.String(50)),
        sa.Column('confidence', sa.Integer, default=50),
        sa.Column('occurrences', sa.Integer, default=1),

        # Pattern Data
        sa.Column('data', JSONB, default={}),
        sa.Column('predictions', JSONB, default=[]),

        # Status
        sa.Column('is_active', sa.Boolean, default=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create twin_actions table
    op.create_table(
        'twin_actions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('twin_profile_id', UUID(as_uuid=True), sa.ForeignKey('twin_profiles.id'), nullable=False),

        # Action Info
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('priority', sa.Integer, default=3),
        sa.Column('title', sa.String(255)),
        sa.Column('description', sa.Text),
        sa.Column('data', JSONB, default={}),

        # Scheduling
        sa.Column('scheduled_for', sa.String(50)),
        sa.Column('executed_at', sa.String(50)),

        # Status
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('result', JSONB),

        # Approval
        sa.Column('requires_approval', sa.Boolean, default=False),
        sa.Column('user_notified', sa.Boolean, default=False),
        sa.Column('approved_at', sa.String(50)),
        sa.Column('rejected_at', sa.String(50)),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes for better query performance
    op.create_index('ix_twin_contacts_email', 'twin_contacts', ['email'])
    op.create_index('ix_twin_contacts_is_vip', 'twin_contacts', ['is_vip'])
    op.create_index('ix_twin_projects_status', 'twin_projects', ['status'])
    op.create_index('ix_twin_learning_events_event_type', 'twin_learning_events', ['event_type'])
    op.create_index('ix_twin_patterns_pattern_type', 'twin_patterns', ['pattern_type'])
    op.create_index('ix_twin_actions_status', 'twin_actions', ['status'])
    op.create_index('ix_twin_actions_action_type', 'twin_actions', ['action_type'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_twin_actions_action_type', 'twin_actions')
    op.drop_index('ix_twin_actions_status', 'twin_actions')
    op.drop_index('ix_twin_patterns_pattern_type', 'twin_patterns')
    op.drop_index('ix_twin_learning_events_event_type', 'twin_learning_events')
    op.drop_index('ix_twin_projects_status', 'twin_projects')
    op.drop_index('ix_twin_contacts_is_vip', 'twin_contacts')
    op.drop_index('ix_twin_contacts_email', 'twin_contacts')

    # Drop tables
    op.drop_table('twin_actions')
    op.drop_table('twin_patterns')
    op.drop_table('twin_learning_events')
    op.drop_table('twin_projects')
    op.drop_table('twin_contacts')
    op.drop_table('twin_profiles')
