@echo off
echo 🎙️  Ollama STT Docker Setup
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker daemon is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker daemon is not running
    echo Please start Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker is available and running
echo.

REM Build the Docker image
echo 🔨 Building Docker image...
docker build -t ollama-stt .
if errorlevel 1 (
    echo ❌ Docker build failed
    pause
    exit /b 1
)

echo ✅ Docker image built successfully
echo.

REM Run the container
echo 🚀 Starting Docker container...
echo Use Ctrl+C to stop the container
echo.

docker run --rm -it ^
    -v "%CD%\transcriptions:/app/transcriptions" ^
    -v "%CD%\uploads:/app/uploads" ^
    ollama-stt %*

echo.
echo 📝 Container stopped
pause
