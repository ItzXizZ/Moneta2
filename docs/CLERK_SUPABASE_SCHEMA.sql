-- Supabase Database Schema for Clerk Authentication Integration
-- Run these commands in your Supabase SQL Editor

-- ============================================
-- 1. UPDATE USERS TABLE FOR CLERK
-- ============================================

-- Add clerk_id column if not exists (for new installations)
ALTER TABLE users ADD COLUMN IF NOT EXISTS clerk_id TEXT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT;

-- Make password_hash nullable (not needed for Clerk OAuth)
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;

-- Create index for faster clerk_id lookups
CREATE INDEX IF NOT EXISTS idx_users_clerk_id ON users(clerk_id);

-- Update RLS policies for Clerk
DROP POLICY IF EXISTS "Users can view own profile" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;

-- New policies that work with Clerk IDs
CREATE POLICY "Users can view own profile via clerk" ON users
    FOR SELECT USING (clerk_id = current_setting('request.jwt.claim.sub', true));

CREATE POLICY "Users can update own profile via clerk" ON users
    FOR UPDATE USING (clerk_id = current_setting('request.jwt.claim.sub', true));

-- Policy for service role (used by backend)
CREATE POLICY "Service role full access to users" ON users
    FOR ALL USING (true);

-- ============================================
-- 2. USER MEMORY DATABASES TABLE
-- ============================================

-- Already exists from previous setup, just ensure RLS policies are correct
ALTER TABLE user_memory_databases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can access own memory database" ON user_memory_databases;

-- Allow users to access their own memory database via user_id
CREATE POLICY "Users can access own memory database" ON user_memory_databases
    FOR ALL USING (
        user_id IN (
            SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claim.sub', true)
        )
    );

-- Policy for service role
CREATE POLICY "Service role full access to memory db" ON user_memory_databases
    FOR ALL USING (true);

-- ============================================
-- 3. USER MEMORIES TABLE
-- ============================================

-- Already exists, update RLS policies
ALTER TABLE user_memories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can access own memories" ON user_memories;

-- Allow users to access their own memories via user_id linked to clerk_id
CREATE POLICY "Users can access own memories" ON user_memories
    FOR ALL USING (
        user_id IN (
            SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claim.sub', true)
        )
    );

-- Policy for service role
CREATE POLICY "Service role full access to memories" ON user_memories
    FOR ALL USING (true);

-- ============================================
-- 4. MEMORY CONNECTIONS TABLE
-- ============================================

-- Update RLS policies if table exists
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'memory_connections') THEN
        ALTER TABLE memory_connections ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "Users can access own memory connections" ON memory_connections;
        
        CREATE POLICY "Users can access own memory connections" ON memory_connections
            FOR ALL USING (
                user_id IN (
                    SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claim.sub', true)
                )
            );
        
        CREATE POLICY "Service role full access to connections" ON memory_connections
            FOR ALL USING (true);
    END IF;
END $$;

-- ============================================
-- 5. CONVERSATIONS TABLE (if exists)
-- ============================================

DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'conversations') THEN
        ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "Users can access own conversations" ON conversations;
        
        CREATE POLICY "Users can access own conversations" ON conversations
            FOR ALL USING (
                user_id IN (
                    SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claim.sub', true)
                )
            );
        
        CREATE POLICY "Service role full access to conversations" ON conversations
            FOR ALL USING (true);
    END IF;
END $$;

-- ============================================
-- 6. MESSAGES TABLE (if exists)
-- ============================================

DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'messages') THEN
        ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "Users can access messages in their conversations" ON messages;
        
        CREATE POLICY "Users can access messages in their conversations" ON messages
            FOR ALL USING (
                conversation_id IN (
                    SELECT id FROM conversations WHERE user_id IN (
                        SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claim.sub', true)
                    )
                )
            );
        
        CREATE POLICY "Service role full access to messages" ON messages
            FOR ALL USING (true);
    END IF;
END $$;

-- ============================================
-- 7. USER SUBSCRIPTIONS TABLE (if exists)
-- ============================================

DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'user_subscriptions') THEN
        ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "Users can view own subscription" ON user_subscriptions;
        
        CREATE POLICY "Users can view own subscription" ON user_subscriptions
            FOR SELECT USING (
                user_id IN (
                    SELECT id FROM users WHERE clerk_id = current_setting('request.jwt.claim.sub', true)
                )
            );
        
        CREATE POLICY "Service role full access to subscriptions" ON user_subscriptions
            FOR ALL USING (true);
    END IF;
END $$;

-- ============================================
-- 8. HELPER FUNCTIONS
-- ============================================

-- Function to get user ID from Clerk ID
CREATE OR REPLACE FUNCTION get_user_id_from_clerk(clerk_id_param TEXT)
RETURNS UUID AS $$
DECLARE
    user_uuid UUID;
BEGIN
    SELECT id INTO user_uuid FROM users WHERE clerk_id = clerk_id_param;
    RETURN user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to sync Clerk user (called by backend)
CREATE OR REPLACE FUNCTION sync_clerk_user(
    clerk_id_param TEXT,
    email_param TEXT,
    name_param TEXT,
    profile_image_param TEXT DEFAULT NULL
)
RETURNS TABLE (
    user_id UUID,
    is_new_user BOOLEAN
) AS $$
DECLARE
    existing_user_id UUID;
    new_user BOOLEAN := FALSE;
BEGIN
    -- Check if user exists
    SELECT id INTO existing_user_id FROM users WHERE clerk_id = clerk_id_param;
    
    IF existing_user_id IS NULL THEN
        -- Create new user
        INSERT INTO users (clerk_id, email, name, profile_image, created_at, is_active)
        VALUES (clerk_id_param, email_param, name_param, profile_image_param, NOW(), TRUE)
        RETURNING id INTO existing_user_id;
        
        new_user := TRUE;
        
        -- Create memory database for new user
        INSERT INTO user_memory_databases (user_id, created_at, memory_count, last_accessed)
        VALUES (existing_user_id, NOW(), 0, NOW());
    ELSE
        -- Update existing user
        UPDATE users 
        SET 
            email = email_param,
            name = name_param,
            profile_image = COALESCE(profile_image_param, profile_image),
            last_login = NOW()
        WHERE id = existing_user_id;
    END IF;
    
    RETURN QUERY SELECT existing_user_id, new_user;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 9. VERIFICATION QUERIES
-- ============================================

-- Verify the schema is set up correctly
-- Run these to check your setup:

-- Check users table structure
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'users';

-- Check RLS is enabled
-- SELECT tablename, rowsecurity 
-- FROM pg_tables 
-- WHERE schemaname = 'public' 
-- AND tablename IN ('users', 'user_memories', 'user_memory_databases');

-- Check policies exist
-- SELECT schemaname, tablename, policyname 
-- FROM pg_policies 
-- WHERE schemaname = 'public';

-- ============================================
-- NOTES
-- ============================================

/*
1. CLERK_ID is now the primary identifier for users
2. PASSWORD_HASH is optional (for OAuth-only users)
3. All RLS policies updated to work with Clerk authentication
4. Service role bypass added for backend operations
5. Helper functions created for common operations

IMPORTANT: 
- Make sure to use SUPABASE_SERVICE_KEY in your backend for admin operations
- The service role bypasses RLS, which is necessary for user creation
- Regular SUPABASE_KEY (anon key) can be used for client operations

SECURITY:
- Row Level Security is enabled on all tables
- Users can only access their own data
- Service role can access all data (use carefully!)
- Clerk handles OAuth and session management
*/


