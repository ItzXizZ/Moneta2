@echo off
set SUPABASE_URL=https://pquleppdqequfjwlcmbn.supabase.co
set SUPABASE_KEY=%SUPABASE_KEY%
set JWT_SECRET=%JWT_SECRET%
set OPENAI_API_KEY=%OPENAI_API_KEY%

echo 🔧 Setting up chat tables in Supabase...
echo.
echo Please make sure you have set your OPENAI_API_KEY environment variable
echo.
echo ⚠️  IMPORTANT: Please manually run the SQL script in your Supabase dashboard:
echo.
echo 1. Go to https://pquleppdqequfjwlcmbn.supabase.co
echo 2. Login to your Supabase dashboard
echo 3. Go to SQL Editor
echo 4. Copy and paste the contents of create_chat_tables.sql
echo 5. Click "Run" to execute the SQL
echo.
echo The SQL script will create:
echo - user_chat_threads table
echo - user_chat_messages table  
echo - Indexes for performance
echo - Triggers for automatic timestamps
echo.
echo After running the SQL, the chat history will be stored in Supabase!
echo.
python setup_chat_tables.py
pause 