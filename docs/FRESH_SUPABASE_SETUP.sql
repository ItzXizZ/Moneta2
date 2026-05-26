-- =============================================================================
-- Moneta2 — Fresh Supabase Setup (run on a brand-new project)
-- =============================================================================
-- 1. Create a new project at https://supabase.com
-- 2. Open SQL Editor → New query → paste this entire file → Run
-- 3. Copy Project URL, anon key, and service_role key into your .env
-- =============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- 1. USERS
-- =============================================================================
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    clerk_id TEXT UNIQUE,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    profile_image TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_clerk_id ON users(clerk_id);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile via clerk" ON users
    FOR SELECT USING (clerk_id = current_setting('request.jwt.claim.sub', true));

CREATE POLICY "Users can update own profile via clerk" ON users
    FOR UPDATE USING (clerk_id = current_setting('request.jwt.claim.sub', true));

CREATE POLICY "Service role full access to users" ON users
    FOR ALL USING (true);

-- =============================================================================
-- 2. USER MEMORY DATABASES
-- =============================================================================
CREATE TABLE user_memory_databases (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    memory_count INTEGER DEFAULT 0,
    UNIQUE(user_id)
);

ALTER TABLE user_memory_databases ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own memory database" ON user_memory_databases
    FOR ALL USING (
        user_id IN (
            SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claim.sub', true)
        )
    );

CREATE POLICY "Service role full access to memory db" ON user_memory_databases
    FOR ALL USING (true);

-- =============================================================================
-- 3. USER MEMORIES
-- =============================================================================
CREATE TABLE user_memories (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    score DECIMAL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    embedding VECTOR(768)
);

CREATE INDEX idx_user_memories_user_id ON user_memories(user_id);
CREATE INDEX idx_user_memories_score ON user_memories(user_id, score DESC);
CREATE INDEX idx_user_memories_created_at ON user_memories(user_id, created_at DESC);
CREATE INDEX idx_user_memories_content_search ON user_memories USING gin(to_tsvector('english', content));

ALTER TABLE user_memories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own memories" ON user_memories
    FOR ALL USING (
        user_id IN (
            SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claim.sub', true)
        )
    );

CREATE POLICY "Service role full access to memories" ON user_memories
    FOR ALL USING (true);

-- =============================================================================
-- 4. MEMORY CONNECTIONS
-- =============================================================================
CREATE TABLE memory_connections (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    from_memory_id UUID REFERENCES user_memories(id) ON DELETE CASCADE,
    to_memory_id UUID REFERENCES user_memories(id) ON DELETE CASCADE,
    similarity_score DECIMAL NOT NULL,
    connection_type TEXT DEFAULT 'semantic',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, from_memory_id, to_memory_id)
);

CREATE INDEX idx_memory_connections_user_id ON memory_connections(user_id);
CREATE INDEX idx_memory_connections_from_memory ON memory_connections(from_memory_id);
CREATE INDEX idx_memory_connections_similarity ON memory_connections(user_id, similarity_score DESC);

ALTER TABLE memory_connections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own memory connections" ON memory_connections
    FOR ALL USING (
        user_id IN (
            SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claim.sub', true)
        )
    );

CREATE POLICY "Service role full access to connections" ON memory_connections
    FOR ALL USING (true);

-- =============================================================================
-- 5. CHAT THREADS & MESSAGES
-- =============================================================================
CREATE TABLE user_chat_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    thread_id TEXT NOT NULL UNIQUE,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE user_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id TEXT NOT NULL REFERENCES user_chat_threads(thread_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    sender TEXT NOT NULL CHECK (sender IN ('user', 'assistant')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    memory_context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_chat_threads_user_id ON user_chat_threads(user_id);
CREATE INDEX idx_user_chat_threads_thread_id ON user_chat_threads(thread_id);
CREATE INDEX idx_user_chat_messages_thread_id ON user_chat_messages(thread_id);
CREATE INDEX idx_user_chat_messages_user_id ON user_chat_messages(user_id);
CREATE INDEX idx_user_chat_messages_timestamp ON user_chat_messages(timestamp);

ALTER TABLE user_chat_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_chat_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own chat threads" ON user_chat_threads
    FOR ALL USING (
        user_id IN (
            SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claim.sub', true)
        )
    );

CREATE POLICY "Service role full access to chat threads" ON user_chat_threads
    FOR ALL USING (true);

CREATE POLICY "Users can access own chat messages" ON user_chat_messages
    FOR ALL USING (
        user_id IN (
            SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claim.sub', true)
        )
    );

CREATE POLICY "Service role full access to chat messages" ON user_chat_messages
    FOR ALL USING (true);

-- =============================================================================
-- 6. SUBSCRIPTIONS
-- =============================================================================
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    price_cents INTEGER NOT NULL,
    monthly_message_limit INTEGER,
    features JSONB NOT NULL DEFAULT '{}',
    ai_model TEXT NOT NULL DEFAULT 'gpt-4o-mini',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES subscription_plans(id),
    status TEXT NOT NULL CHECK (status IN ('active', 'cancelled', 'expired', 'trial')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    stripe_subscription_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, plan_id)
);

CREATE TABLE user_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    month_year TEXT NOT NULL,
    messages_used INTEGER DEFAULT 0,
    api_calls_used INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    last_reset TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, month_year)
);

CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX idx_user_subscriptions_expires_at ON user_subscriptions(expires_at);
CREATE INDEX idx_user_usage_user_id ON user_usage(user_id);
CREATE INDEX idx_user_usage_month_year ON user_usage(month_year);

ALTER TABLE subscription_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view active subscription plans" ON subscription_plans
    FOR SELECT USING (is_active = TRUE);

CREATE POLICY "Service role full access to subscription plans" ON subscription_plans
    FOR ALL USING (true);

CREATE POLICY "Users can view own subscriptions" ON user_subscriptions
    FOR SELECT USING (
        user_id IN (
            SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claim.sub', true)
        )
    );

CREATE POLICY "Service role full access to user subscriptions" ON user_subscriptions
    FOR ALL USING (true);

CREATE POLICY "Users can view own usage" ON user_usage
    FOR SELECT USING (
        user_id IN (
            SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claim.sub', true)
        )
    );

CREATE POLICY "Service role full access to user usage" ON user_usage
    FOR ALL USING (true);

INSERT INTO subscription_plans (name, price_cents, monthly_message_limit, features, ai_model) VALUES
('free', 0, 50, '{"memory_limit": 100, "features": ["basic_chat", "memory_storage"]}', 'gpt-4o-mini'),
('premium', 2000, NULL, '{"memory_limit": null, "features": ["advanced_chat", "unlimited_memory", "priority_support", "gpt4_access"]}', 'gpt-3.5-turbo')
ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- 7. FUNCTIONS & TRIGGERS
-- =============================================================================

CREATE OR REPLACE FUNCTION update_memory_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE user_memory_databases
        SET memory_count = memory_count + 1, last_accessed = NOW()
        WHERE user_id = NEW.user_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE user_memory_databases
        SET memory_count = memory_count - 1, last_accessed = NOW()
        WHERE user_id = OLD.user_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_memory_count_insert
    AFTER INSERT ON user_memories
    FOR EACH ROW EXECUTE FUNCTION update_memory_count();

CREATE TRIGGER trigger_update_memory_count_delete
    AFTER DELETE ON user_memories
    FOR EACH ROW EXECUTE FUNCTION update_memory_count();

CREATE OR REPLACE FUNCTION initialize_user_memory_database()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_memory_databases (user_id)
    VALUES (NEW.id)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_initialize_user_memory_database
    AFTER INSERT ON users
    FOR EACH ROW EXECUTE FUNCTION initialize_user_memory_database();

CREATE OR REPLACE FUNCTION update_chat_thread_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_chat_message_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_thread_timestamp
    BEFORE UPDATE ON user_chat_threads
    FOR EACH ROW EXECUTE FUNCTION update_chat_thread_updated_at();

CREATE TRIGGER update_message_timestamp
    BEFORE UPDATE ON user_chat_messages
    FOR EACH ROW EXECUTE FUNCTION update_chat_message_updated_at();

CREATE OR REPLACE FUNCTION update_subscription_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_subscriptions_updated_at
    BEFORE UPDATE ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_subscription_updated_at();

CREATE TRIGGER trigger_update_user_usage_updated_at
    BEFORE UPDATE ON user_usage
    FOR EACH ROW EXECUTE FUNCTION update_subscription_updated_at();

CREATE OR REPLACE FUNCTION get_user_id_from_clerk(clerk_id_param TEXT)
RETURNS UUID AS $$
DECLARE
    user_uuid UUID;
BEGIN
    SELECT id INTO user_uuid FROM users WHERE clerk_id = clerk_id_param;
    RETURN user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION sync_clerk_user(
    clerk_id_param TEXT,
    email_param TEXT,
    name_param TEXT,
    profile_image_param TEXT DEFAULT NULL
)
RETURNS TABLE (user_id UUID, is_new_user BOOLEAN) AS $$
DECLARE
    existing_user_id UUID;
    new_user BOOLEAN := FALSE;
BEGIN
    SELECT id INTO existing_user_id FROM users WHERE clerk_id = clerk_id_param;

    IF existing_user_id IS NULL THEN
        INSERT INTO users (clerk_id, email, name, profile_image, created_at, is_active)
        VALUES (clerk_id_param, email_param, name_param, profile_image_param, NOW(), TRUE)
        RETURNING id INTO existing_user_id;
        new_user := TRUE;
    ELSE
        UPDATE users
        SET email = email_param,
            name = name_param,
            profile_image = COALESCE(profile_image_param, profile_image),
            last_login = NOW()
        WHERE id = existing_user_id;
    END IF;

    RETURN QUERY SELECT existing_user_id, new_user;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_user_subscription(user_id_param UUID)
RETURNS TABLE (
    plan_name TEXT,
    price_cents INTEGER,
    monthly_message_limit INTEGER,
    features JSONB,
    ai_model TEXT,
    status TEXT,
    expires_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        sp.name,
        sp.price_cents,
        sp.monthly_message_limit,
        sp.features,
        sp.ai_model,
        COALESCE(us.status, 'free') AS status,
        us.expires_at
    FROM subscription_plans sp
    LEFT JOIN user_subscriptions us ON sp.id = us.plan_id
        AND us.user_id = user_id_param
        AND us.status = 'active'
        AND (us.expires_at IS NULL OR us.expires_at > NOW())
    WHERE sp.name = COALESCE(
        (SELECT plan.name FROM subscription_plans plan
         JOIN user_subscriptions sub ON plan.id = sub.plan_id
         WHERE sub.user_id = user_id_param
         AND sub.status = 'active'
         AND (sub.expires_at IS NULL OR sub.expires_at > NOW())
         LIMIT 1),
        'free'
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION track_user_usage(
    user_id_param UUID,
    messages_increment INTEGER DEFAULT 1,
    api_calls_increment INTEGER DEFAULT 1,
    tokens_increment INTEGER DEFAULT 0
)
RETURNS VOID AS $$
DECLARE
    current_month TEXT;
BEGIN
    current_month := TO_CHAR(NOW(), 'YYYY-MM');

    INSERT INTO user_usage (user_id, month_year, messages_used, api_calls_used, tokens_used)
    VALUES (user_id_param, current_month, messages_increment, api_calls_increment, tokens_increment)
    ON CONFLICT (user_id, month_year)
    DO UPDATE SET
        messages_used = user_usage.messages_used + messages_increment,
        api_calls_used = user_usage.api_calls_used + api_calls_increment,
        tokens_used = user_usage.tokens_used + tokens_increment,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION check_user_limits(user_id_param UUID)
RETURNS TABLE (
    can_use_service BOOLEAN,
    messages_used INTEGER,
    messages_limit INTEGER,
    plan_name TEXT
) AS $$
DECLARE
    current_month TEXT;
    user_subscription RECORD;
    usage_record RECORD;
BEGIN
    current_month := TO_CHAR(NOW(), 'YYYY-MM');

    SELECT * INTO user_subscription FROM get_user_subscription(user_id_param) LIMIT 1;

    SELECT * INTO usage_record FROM user_usage
    WHERE user_id = user_id_param AND month_year = current_month;

    IF usage_record IS NULL THEN
        INSERT INTO user_usage (user_id, month_year, messages_used, api_calls_used, tokens_used)
        VALUES (user_id_param, current_month, 0, 0, 0);
        usage_record.messages_used := 0;
    END IF;

    RETURN QUERY
    SELECT
        CASE
            WHEN user_subscription.monthly_message_limit IS NULL THEN TRUE
            ELSE usage_record.messages_used < user_subscription.monthly_message_limit
        END AS can_use_service,
        COALESCE(usage_record.messages_used, 0) AS messages_used,
        user_subscription.monthly_message_limit,
        user_subscription.plan_name;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 8. VERIFY (optional — run separately to confirm setup)
-- =============================================================================
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
-- SELECT name, price_cents FROM subscription_plans;
