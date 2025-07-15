@echo off
echo 🚀 Starting Ollama STT Web Portal...
echo 📦 Dependencies will be automatically installed if missing
echo.

REM Check if we're in the correct directory (.ollama)
if not exist "models" (
    echo ⚠️  WARNING: This script should be run from your .ollama directory
    echo Expected location: C:\Users\%USERNAME%\.ollama
    echo Current location: %CD%
    echo.
    echo The application may not work correctly from this location.
    echo Please move the repository to your .ollama directory.
    echo.
    pause
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

REM Dependencies will be automatically installed by the Python script
echo 💡 Dependencies will be automatically checked and installed by the application

REM Check if Ollama is running
echo 🤖 Checking Ollama status...
ollama list >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Ollama is not running or not installed
    echo To use Ollama integration, please:
    echo 1. Install Ollama from https://ollama.ai
    echo 2. Run: ollama serve
    echo 3. Pull a model: ollama pull llama3.1
    echo.
    echo The web portal will still work for speech-to-text without Ollama
    echo.
)

REM Create directories
if not exist "uploads" mkdir uploads
if not exist "transcriptions" mkdir transcriptions

echo 🌐 Starting web server...
echo.
echo 📡 Web Portal will be available at: http://localhost:55667
echo 🎙️  Make sure your microphone is connected and working
echo 🔊 Audio file formats supported: WAV, MP3, FLAC, OGG
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the Flask application
python web_portal.py

pause
