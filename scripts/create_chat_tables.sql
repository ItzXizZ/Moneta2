-- Create chat threads table for user-specific conversation history
CREATE TABLE IF NOT EXISTS user_chat_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    thread_id TEXT NOT NULL UNIQUE,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Create chat messages table for storing individual messages
CREATE TABLE IF NOT EXISTS user_chat_messages (
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_chat_threads_user_id ON user_chat_threads(user_id);
CREATE INDEX IF NOT EXISTS idx_user_chat_threads_thread_id ON user_chat_threads(thread_id);
CREATE INDEX IF NOT EXISTS idx_user_chat_messages_thread_id ON user_chat_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_user_chat_messages_user_id ON user_chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_user_chat_messages_timestamp ON user_chat_messages(timestamp);

-- Create function to automatically update updated_at timestamp for threads
CREATE OR REPLACE FUNCTION update_chat_thread_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create function to automatically update updated_at timestamp for messages
CREATE OR REPLACE FUNCTION update_chat_message_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at when thread is modified
CREATE TRIGGER update_thread_timestamp
    BEFORE UPDATE ON user_chat_threads
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_thread_updated_at();

-- Create trigger to automatically update updated_at when messages are modified
CREATE TRIGGER update_message_timestamp
    BEFORE UPDATE ON user_chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_message_updated_at();

-- Add some helpful comments
COMMENT ON TABLE user_chat_threads IS 'Stores user-specific chat conversation threads';
COMMENT ON TABLE user_chat_messages IS 'Stores individual messages within chat threads';
COMMENT ON COLUMN user_chat_messages.memory_context IS 'JSON array of memory contexts used for AI responses';
COMMENT ON COLUMN user_chat_messages.sender IS 'Either "user" or "assistant"'; 