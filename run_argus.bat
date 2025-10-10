@echo off
echo Starting Argus - The All-Seeing Photo Renamer...

REM Change to the directory where this batch file is located
cd /d "%~dp0"

REM Check if Docker Desktop is running
echo Checking Docker Desktop status...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker Desktop is not running. Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

    REM Wait for Docker to be ready
    echo Waiting for Docker to be ready...
    :wait_loop
    timeout /t 2 /nobreak >nul
    docker info >nul 2>&1
    if %errorlevel% neq 0 goto wait_loop

    echo Docker Desktop is now running!
) else (
    echo Docker Desktop is already running.
)

echo.
streamlit run main.py --browser.gatherUsageStats false
pause
