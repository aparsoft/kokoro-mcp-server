@echo off
REM Aparsoft TTS - Streamlit App Launcher (Windows)
REM Quick startup script for the Streamlit management interface

echo =========================================
echo 🎙️  Aparsoft TTS - Streamlit Manager
echo =========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo ❌ No virtual environment found.
    echo    Create one with: python -m venv venv
    echo    Then activate with: venv\Scripts\activate
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if streamlit is installed
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo ❌ Streamlit not found!
    echo    Installing required packages...
    pip install streamlit plotly pandas soundfile
)

REM Check if aparsoft_tts is installed
python -c "import aparsoft_tts" 2>nul
if errorlevel 1 (
    echo ❌ aparsoft_tts not found!
    echo    Installing package...
    pip install -e .[mcp,cli]
)

echo.
echo ✅ All dependencies ready!
echo.
echo 🚀 Starting Streamlit app...
echo    URL: http://localhost:8501
echo.
echo    Press Ctrl+C to stop the server
echo.
echo =========================================

REM Create required directories
if not exist "outputs\single" mkdir outputs\single
if not exist "outputs\batch" mkdir outputs\batch
if not exist "outputs\scripts" mkdir outputs\scripts
if not exist "outputs\voice_samples" mkdir outputs\voice_samples
if not exist "data" mkdir data
if not exist "config" mkdir config
if not exist "temp\scripts" mkdir temp\scripts

REM Start Streamlit
streamlit run streamlit_app.py ^
    --server.port=8501 ^
    --server.address=localhost ^
    --server.headless=false ^
    --browser.gatherUsageStats=false ^
    --theme.base="light" ^
    --theme.primaryColor="#667eea" ^
    --theme.backgroundColor="#ffffff" ^
    --theme.secondaryBackgroundColor="#f0f2f6"
