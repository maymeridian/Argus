@echo off
setlocal enabledelayedexpansion
echo ========================================
echo olmOCR Docker Setup
echo ========================================
echo.
REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed!
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [OK] Docker is installed
echo.
REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo [OK] Docker is running
echo.
REM Check if docker compose is available
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not available!
    echo Please update Docker Desktop to the latest version.
    pause
    exit /b 1
)
echo [OK] Docker Compose is available
echo.
REM Check if NVIDIA GPU is available
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo [WARNING] NVIDIA GPU not detected or NVIDIA Container Toolkit not installed!
    echo olmOCR requires a NVIDIA GPU with CUDA support.
    echo.
    echo If you have a NVIDIA GPU, please install NVIDIA Container Toolkit:
    echo https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "!continue!"=="y" (
        echo Setup cancelled.
        pause
        exit /b 1
    )
) else (
    echo [OK] NVIDIA GPU detected
)
echo.
REM Check if required files exist
if not exist "docker-compose.yml" (
    echo [ERROR] docker-compose.yml not found!
    echo Please ensure you're running this from the project directory.
    pause
    exit /b 1
)
echo [OK] docker-compose.yml found
echo.
if not exist "Dockerfile" (
    echo [ERROR] Dockerfile not found!
    echo Please ensure you're running this from the project directory.
    pause
    exit /b 1
)
echo [OK] Dockerfile found
echo.
if not exist "main.py" (
    echo [ERROR] main.py not found!
    echo Please ensure you're running this from the project directory.
    pause
    exit /b 1
)
echo [OK] main.py found
echo.
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    echo Please ensure you're running this from the project directory.
    pause
    exit /b 1
)
echo [OK] requirements.txt found
echo.
REM Check if Python is installed and install requirements
echo Installing Python requirements locally...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed locally!
    echo Please install Python from https://www.python.org/downloads/
    echo.
    set /p continue="Continue without local installation? (y/n): "
    if /i not "!continue!"=="y" (
        echo Setup cancelled.
        pause
        exit /b 1
    )
    echo Skipping local requirements installation...
) else (
    echo [OK] Python is installed
    echo Installing packages from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [WARNING] Failed to install some requirements locally
        echo The Docker container will still have all dependencies.
        echo.
        set /p continue="Continue anyway? (y/n): "
        if /i not "!continue!"=="y" (
            echo Setup cancelled.
            pause
            exit /b 1
        )
    ) else (
        echo [OK] Local requirements installed successfully
    )
)
echo.
echo ============================================
echo Setup Complete! Run run_argus.bat to start!
echo ============================================
pause