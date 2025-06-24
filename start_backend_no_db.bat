@echo off
echo Starting ScapeGIS Backend without Database...
echo.

REM Set environment variables
set USE_DATABASE=false
set PORT=8001

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Start the server
echo Starting FastAPI server on port 8001...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

pause
