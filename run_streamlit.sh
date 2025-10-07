#!/bin/bash

# Aparsoft TTS - Streamlit App Launcher
# Quick startup script for the Streamlit management interface

echo "========================================="
echo "🎙️  Aparsoft TTS - Streamlit Manager"
echo "========================================="
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   It's recommended to use a virtual environment"
    echo ""
    
    # Check if venv exists
    if [ -d "venv" ]; then
        echo "📦 Found virtual environment. Activating..."
        source venv/bin/activate
    else
        echo "❌ No virtual environment found."
        echo "   Create one with: python -m venv venv"
        echo "   Then activate with: source venv/bin/activate"
        exit 1
    fi
fi

# Check if streamlit is installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "❌ Streamlit not found!"
    echo "   Installing required packages..."
    pip install streamlit plotly pandas soundfile
fi

# Check if aparsoft_tts is installed
if ! python -c "import aparsoft_tts" 2>/dev/null; then
    echo "❌ aparsoft_tts not found!"
    echo "   Installing package..."
    pip install -e ".[mcp,cli]"
fi

echo ""
echo "✅ All dependencies ready!"
echo ""
echo "🚀 Starting Streamlit app..."
echo "   URL: http://localhost:8501"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""
echo "========================================="

# Create required directories
mkdir -p outputs/single outputs/batch outputs/scripts outputs/voice_samples
mkdir -p data config temp/scripts

# Start Streamlit with optimal settings
streamlit run streamlit_app.py \
    --server.port=8501 \
    --server.address=localhost \
    --server.headless=false \
    --browser.gatherUsageStats=false \
    --theme.base="light" \
    --theme.primaryColor="#667eea" \
    --theme.backgroundColor="#ffffff" \
    --theme.secondaryBackgroundColor="#f0f2f6"
