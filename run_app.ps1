# Set environment variables
$env:SUPABASE_URL = "https://pquleppdqequfjwlcmbn.supabase.co"
# $env:SUPABASE_KEY = "your_supabase_key_here"  # Set via .env file instead
$env:JWT_SECRET = $env:JWT_SECRET
$env:OPENAI_API_KEY = $env:OPENAI_API_KEY
$env:FLASK_DEBUG = "true"

# Run the application
Write-Host "🚀 Starting Moneta application..."
Write-Host "📱 Open your browser and go to: http://localhost:4000"
Write-Host "💜 Enjoy your purple-themed chat experience!"

python app.py