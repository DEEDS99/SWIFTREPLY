-- SwiftReply Database Schema
-- Run this to initialise a fresh PostgreSQL database

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Organisations
CREATE TABLE IF NOT EXISTS organisations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'starter' NOT NULL,
    whatsapp_phone_id VARCHAR(100),
    -- Evolution API fields (primary WhatsApp connector)
    evolution_url TEXT,
    evolution_api_key TEXT,
    evolution_instance VARCHAR(255),
    evolution_connected BOOLEAN DEFAULT FALSE,
    whatsapp_token TEXT,
    whatsapp_verify_token VARCHAR(255),
    gemini_api_key TEXT,
    ai_enabled BOOLEAN DEFAULT TRUE,
    ai_system_prompt TEXT DEFAULT 'You are a helpful business assistant. Reply professionally and concisely.',
    monthly_message_limit INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organisation_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'agent' NOT NULL,
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Contacts
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organisation_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    phone_number VARCHAR(30) NOT NULL,
    display_name VARCHAR(255),
    email VARCHAR(255),
    company VARCHAR(255),
    tags JSONB DEFAULT '[]',
    custom_fields JSONB DEFAULT '{}',
    is_blocked BOOLEAN DEFAULT FALSE,
    opted_out BOOLEAN DEFAULT FALSE,
    total_messages INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(organisation_id, phone_number)
);

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organisation_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    assigned_agent_id UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'open',
    last_message_at TIMESTAMP DEFAULT NOW(),
    unread_count INTEGER DEFAULT 0,
    subject VARCHAR(500),
    labels JSONB DEFAULT '[]',
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    whatsapp_message_id VARCHAR(255) UNIQUE,
    direction VARCHAR(20) NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    status VARCHAR(50) DEFAULT 'pending',
    body TEXT,
    media_url TEXT,
    media_mime_type VARCHAR(100),
    media_filename VARCHAR(500),
    media_size BIGINT,
    ai_generated BOOLEAN DEFAULT FALSE,
    ai_analysis TEXT,
    ai_confidence INTEGER,
    template_name VARCHAR(255),
    template_params JSONB DEFAULT '[]',
    reply_to_id UUID REFERENCES messages(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Message Templates
CREATE TABLE IF NOT EXISTS message_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organisation_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    language VARCHAR(10) DEFAULT 'en',
    body TEXT NOT NULL,
    header TEXT,
    footer TEXT,
    variables JSONB DEFAULT '[]',
    whatsapp_template_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'draft',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Analytics Events
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organisation_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_conversations_org ON conversations(organisation_id);
CREATE INDEX IF NOT EXISTS idx_conversations_contact ON conversations(contact_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_contacts_org_phone ON contacts(organisation_id, phone_number);
CREATE INDEX IF NOT EXISTS idx_analytics_org ON analytics_events(organisation_id);
CREATE INDEX IF NOT EXISTS idx_analytics_created ON analytics_events(created_at);

-- Seed: Demo organisation (remove in production)
INSERT INTO organisations (id, name, slug, plan, ai_enabled, ai_system_prompt)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'Demo Company',
    'demo-company',
    'professional',
    TRUE,
    'You are a helpful customer service assistant for Demo Company. Be friendly, professional, and concise. Answer questions about products and services.'
) ON CONFLICT DO NOTHING;

-- Seed: Default templates
INSERT INTO message_templates (organisation_id, name, body, category, status)
VALUES
    ('a0000000-0000-0000-0000-000000000001', 'Welcome Message', 'Hello {{1}}! Welcome to our service. How can we help you today?', 'UTILITY', 'approved'),
    ('a0000000-0000-0000-0000-000000000001', 'Order Confirmation', 'Your order #{{1}} has been confirmed. Estimated delivery: {{2}}. Thank you for your purchase!', 'UTILITY', 'approved'),
    ('a0000000-0000-0000-0000-000000000001', 'Follow Up', 'Hi {{1}}, following up on your recent inquiry. Is there anything else we can help you with?', 'UTILITY', 'draft')
ON CONFLICT DO NOTHING;
