"""Initial schema — all tables

Revision ID: 0001_initial
Revises: 
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        'organisations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('plan', sa.String(50), server_default='starter', nullable=False),
        sa.Column('whatsapp_phone_id', sa.String(100)),
        sa.Column('whatsapp_token', sa.Text()),
        sa.Column('whatsapp_verify_token', sa.String(255)),
        sa.Column('evolution_url', sa.Text()),
        sa.Column('evolution_api_key', sa.Text()),
        sa.Column('evolution_instance', sa.String(255)),
        sa.Column('evolution_connected', sa.Boolean(), server_default='false'),
        sa.Column('gemini_api_key', sa.Text()),
        sa.Column('ai_enabled', sa.Boolean(), server_default='true'),
        sa.Column('ai_system_prompt', sa.Text(), server_default='You are a helpful business assistant. Reply professionally and concisely.'),
        sa.Column('monthly_message_limit', sa.Integer(), server_default='1000'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), server_default='agent', nullable=False),
        sa.Column('avatar_url', sa.Text()),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('last_login', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('phone_number', sa.String(30), nullable=False),
        sa.Column('display_name', sa.String(255)),
        sa.Column('email', sa.String(255)),
        sa.Column('company', sa.String(255)),
        sa.Column('tags', postgresql.JSONB(), server_default='[]'),
        sa.Column('custom_fields', postgresql.JSONB(), server_default='{}'),
        sa.Column('is_blocked', sa.Boolean(), server_default='false'),
        sa.Column('opted_out', sa.Boolean(), server_default='false'),
        sa.Column('total_messages', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('organisation_id', 'phone_number', name='uq_org_phone'),
    )

    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('status', sa.String(50), server_default='open'),
        sa.Column('last_message_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('unread_count', sa.Integer(), server_default='0'),
        sa.Column('subject', sa.String(500)),
        sa.Column('labels', postgresql.JSONB(), server_default='[]'),
        sa.Column('resolved_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('whatsapp_message_id', sa.String(255), unique=True),
        sa.Column('direction', sa.String(20), nullable=False),
        sa.Column('message_type', sa.String(50), server_default='text'),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('body', sa.Text()),
        sa.Column('media_url', sa.Text()),
        sa.Column('media_mime_type', sa.String(100)),
        sa.Column('media_filename', sa.String(500)),
        sa.Column('media_size', sa.BigInteger()),
        sa.Column('ai_generated', sa.Boolean(), server_default='false'),
        sa.Column('ai_analysis', sa.Text()),
        sa.Column('ai_confidence', sa.Integer()),
        sa.Column('template_name', sa.String(255)),
        sa.Column('template_params', postgresql.JSONB(), server_default='[]'),
        sa.Column('reply_to_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('messages.id'), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'message_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('language', sa.String(10), server_default='en'),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('header', sa.Text()),
        sa.Column('footer', sa.Text()),
        sa.Column('variables', postgresql.JSONB(), server_default='[]'),
        sa.Column('whatsapp_template_id', sa.String(255)),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'analytics_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_data', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'broadcast_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('message_body', sa.Text(), nullable=False),
        sa.Column('media_url', sa.Text()),
        sa.Column('message_type', sa.String(50), server_default='text'),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('total_recipients', sa.Integer(), server_default='0'),
        sa.Column('sent_count', sa.Integer(), server_default='0'),
        sa.Column('failed_count', sa.Integer(), server_default='0'),
        sa.Column('scheduled_at', sa.DateTime()),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )

    # Indexes
    op.create_index('idx_conversations_org', 'conversations', ['organisation_id'])
    op.create_index('idx_conversations_contact', 'conversations', ['contact_id'])
    op.create_index('idx_conversations_status', 'conversations', ['status'])
    op.create_index('idx_conversations_last_msg', 'conversations', ['last_message_at'])
    op.create_index('idx_messages_conversation', 'messages', ['conversation_id'])
    op.create_index('idx_messages_created', 'messages', ['created_at'])
    op.create_index('idx_contacts_org_phone', 'contacts', ['organisation_id', 'phone_number'])
    op.create_index('idx_analytics_org', 'analytics_events', ['organisation_id'])
    op.create_index('idx_analytics_created', 'analytics_events', ['created_at'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_org', 'users', ['organisation_id'])


def downgrade() -> None:
    op.drop_table('broadcast_campaigns')
    op.drop_table('analytics_events')
    op.drop_table('message_templates')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('contacts')
    op.drop_table('users')
    op.drop_table('organisations')
