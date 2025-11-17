#!/bin/bash
# Production startup script for Moneta

echo "=========================================="
echo "  Starting Moneta in PRODUCTION mode"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found!"
    echo "Create .env file with production settings"
    exit 1
fi

# Check critical environment variables
source .env

if [ -z "$CLERK_SECRET_KEY" ]; then
    echo "❌ ERROR: CLERK_SECRET_KEY not set in .env"
    exit 1
fi

if [ -z "$SUPABASE_URL" ]; then
    echo "❌ ERROR: SUPABASE_URL not set in .env"
    exit 1
fi

if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" = "your_random_secret_key_here_generate_a_long_random_string" ]; then
    echo "❌ ERROR: JWT_SECRET not properly set!"
    echo "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    exit 1
fi

# Set production environment
export FLASK_DEBUG=False
export ENVIRONMENT=production

echo ""
echo "✓ Environment variables validated"
echo "✓ Starting with Gunicorn..."
echo ""

# Start with Gunicorn
exec gunicorn \
    --workers 4 \
    --threads 2 \
    --bind 0.0.0.0:${PORT:-4000} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    run:app

