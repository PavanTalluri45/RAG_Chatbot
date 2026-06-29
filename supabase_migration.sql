-- Supabase PostgreSQL Migration
-- Creates chat_sessions and messages tables with RLS, triggers, and indices.

-- -------------------------------------------------------------
-- 1. Create Tables
-- -------------------------------------------------------------

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    chatid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New Chat',
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DELETED')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create messages table
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chatid UUID NOT NULL REFERENCES public.chat_sessions(chatid) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    question TEXT,
    answer TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- -------------------------------------------------------------
-- 2. Create Triggers for Automatic updated_at
-- -------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_chat_sessions_updated_at ON public.chat_sessions;
CREATE TRIGGER trigger_chat_sessions_updated_at
    BEFORE UPDATE ON public.chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- -------------------------------------------------------------
-- 3. Enable Row Level Security (RLS)
-- -------------------------------------------------------------

ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- -------------------------------------------------------------
-- 4. Set Up RLS Policies
-- -------------------------------------------------------------

-- Policies for chat_sessions
DROP POLICY IF EXISTS "Users can read their own chat sessions" ON public.chat_sessions;
CREATE POLICY "Users can read their own chat sessions"
    ON public.chat_sessions FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own chat sessions" ON public.chat_sessions;
CREATE POLICY "Users can insert their own chat sessions"
    ON public.chat_sessions FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own chat sessions" ON public.chat_sessions;
CREATE POLICY "Users can update their own chat sessions"
    ON public.chat_sessions FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policies for messages
DROP POLICY IF EXISTS "Users can read their own messages" ON public.messages;
CREATE POLICY "Users can read their own messages"
    ON public.messages FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own messages" ON public.messages;
CREATE POLICY "Users can insert their own messages"
    ON public.messages FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- -------------------------------------------------------------
-- 5. Create Performance Indexes
-- -------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id_status ON public.chat_sessions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_messages_chatid ON public.messages(chatid);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON public.messages(user_id);
