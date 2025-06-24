@echo off
echo ========================================
echo Starting ScapeGIS Backend Server
echo ========================================

cd /d "c:\Users\HP VICTUS\scapegis-backend"

echo Activating virtual environment...
call venv\Scripts\activate

echo Setting environment variables...
set GOOGLE_CLIENT_ID=940830341579-0fcheup5gm7naos0cubblmueftb6viqp.apps.googleusercontent.com
set GOOGLE_CLIENT_SECRET=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
set FRONTEND_URL=http://localhost:3001
set GOOGLE_REDIRECT_URI=http://localhost:8001/api/v1/auth/oauth/callback/google
set GITHUB_REDIRECT_URI=http://localhost:8001/api/v1/auth/oauth/callback/github

echo Note: Database is optional for OAuth testing
echo OAuth will work without database configuration

echo Environment variables set:
echo Google Client ID: %GOOGLE_CLIENT_ID%
echo Frontend URL: %FRONTEND_URL%

echo Starting server on port 8001...
echo Server will be available at: http://localhost:8001
echo OAuth endpoints:
echo   - Google: http://localhost:8001/api/v1/auth/oauth/google
echo   - Status: http://localhost:8001/api/v1/auth/oauth/status
echo   - API Docs: http://localhost:8001/docs
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

pause
