@echo off
set SUPABASE_URL=https://pquleppdqequfjwlcmbn.supabase.co
set SUPABASE_KEY=%SUPABASE_KEY%
set JWT_SECRET=%JWT_SECRET%
set OPENAI_API_KEY=%OPENAI_API_KEY%

echo 🧪 Adding test memories to your account...
echo Please make sure you have set your OPENAI_API_KEY environment variable
python add_test_memories.py
pause 