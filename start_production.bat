@echo off
REM Production startup script for Moneta (Windows)

echo ==========================================
echo   Starting Moneta in PRODUCTION mode
echo ==========================================

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Create .env file with production settings
    pause
    exit /b 1
)

echo.
echo Checking environment variables...

REM Set production environment
set FLASK_DEBUG=False
set ENVIRONMENT=production

echo.
echo Starting with Gunicorn...
echo Note: Make sure Gunicorn is installed: pip install gunicorn
echo.

REM Start with Gunicorn
gunicorn --workers 4 --threads 2 --bind 0.0.0.0:4000 --timeout 120 --access-logfile - --error-logfile - --log-level info run:app

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start Gunicorn
    echo Make sure it's installed: pip install gunicorn
    pause
)

