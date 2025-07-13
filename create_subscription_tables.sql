-- Subscription plans table
CREATE TABLE IF NOT EXISTS subscription_plans (
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

-- User subscriptions table
CREATE TABLE IF NOT EXISTS user_subscriptions (
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

-- Usage tracking table
CREATE TABLE IF NOT EXISTS user_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    month_year TEXT NOT NULL, -- Format: YYYY-MM
    messages_used INTEGER DEFAULT 0,
    api_calls_used INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    last_reset TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, month_year)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_expires_at ON user_subscriptions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_usage_user_id ON user_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_user_usage_month_year ON user_usage(month_year);

-- Enable Row Level Security
ALTER TABLE subscription_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_usage ENABLE ROW LEVEL SECURITY;

-- Policies for subscription_plans (readable by all authenticated users)
CREATE POLICY "Anyone can view subscription plans" ON subscription_plans
    FOR SELECT TO authenticated USING (is_active = TRUE);

-- Policies for user_subscriptions (users can only see their own)
CREATE POLICY "Users can view own subscriptions" ON user_subscriptions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own subscriptions" ON user_subscriptions
    FOR UPDATE USING (auth.uid() = user_id);

-- Policies for user_usage (users can only see their own)
CREATE POLICY "Users can view own usage" ON user_usage
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own usage" ON user_usage
    FOR UPDATE USING (auth.uid() = user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_subscription_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for automatic timestamp updates
CREATE TRIGGER trigger_update_user_subscriptions_updated_at
    BEFORE UPDATE ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_subscription_updated_at();

CREATE TRIGGER trigger_update_user_usage_updated_at
    BEFORE UPDATE ON user_usage
    FOR EACH ROW EXECUTE FUNCTION update_subscription_updated_at();

-- Insert default subscription plans
INSERT INTO subscription_plans (name, price_cents, monthly_message_limit, features, ai_model) VALUES
('free', 0, 50, '{"memory_limit": 100, "features": ["basic_chat", "memory_storage"]}', 'gpt-4o-mini'),
('premium', 2000, NULL, '{"memory_limit": null, "features": ["advanced_chat", "unlimited_memory", "priority_support", "gpt4_access"]}', 'gpt-3.5-turbo')
ON CONFLICT (name) DO NOTHING;

-- Function to get user's current subscription with fallback to free
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
        COALESCE(us.status, 'free') as status,
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

-- Function to track usage
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

-- Function to check if user has exceeded limits
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
    
    -- Get user's subscription
    SELECT * INTO user_subscription FROM get_user_subscription(user_id_param) LIMIT 1;
    
    -- Get current usage
    SELECT * INTO usage_record FROM user_usage 
    WHERE user_id = user_id_param AND month_year = current_month;
    
    -- If no usage record, create one
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
        END as can_use_service,
        COALESCE(usage_record.messages_used, 0) as messages_used,
        user_subscription.monthly_message_limit,
        user_subscription.plan_name;
END;
$$ LANGUAGE plpgsql; 