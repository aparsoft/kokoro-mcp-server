# run_streamlit.py

"""
Aparsoft TTS - Streamlit App Launcher (Cross-platform)

Universal launcher for the Streamlit management interface
Works on Windows, macOS, and Linux
"""

import sys
import subprocess
from pathlib import Path
import importlib.util

def check_package(package_name):
    """Check if a package is installed"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_package(package):
    """Install a package using pip"""
    print(f"📦 Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def create_directories():
    """Create required output directories"""
    directories = [
        "outputs/single",
        "outputs/batch",
        "outputs/scripts",
        "outputs/voice_samples",
        "data",
        "config",
        "temp/scripts"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def main():
    print("=" * 50)
    print("🎙️  Aparsoft TTS - Streamlit Manager")
    print("=" * 50)
    print()
    
    # Check and install dependencies
    print("🔍 Checking dependencies...")
    
    required_packages = [
        ("streamlit", "streamlit"),
        ("plotly", "plotly"),
        ("pandas", "pandas"),
        ("soundfile", "soundfile"),
    ]
    
    for module_name, package_name in required_packages:
        if not check_package(module_name):
            print(f"❌ {package_name} not found!")
            install_package(package_name)
        else:
            print(f"✅ {package_name} installed")
    
    # Check aparsoft_tts
    if not check_package("aparsoft_tts"):
        print("❌ aparsoft_tts not found!")
        print("   Installing package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", ".[mcp,cli]"])
    else:
        print("✅ aparsoft_tts installed")
    
    print()
    print("✅ All dependencies ready!")
    print()
    
    # Create directories
    print("📁 Creating output directories...")
    create_directories()
    print("✅ Directories created")
    print()
    
    # Start Streamlit
    print("🚀 Starting Streamlit app...")
    print("   URL: http://localhost:8501")
    print()
    print("   Press Ctrl+C to stop the server")
    print()
    print("=" * 50)
    print()
    
    # Run Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
        "--server.port=8501",
        "--server.address=localhost",
        "--server.headless=false",
        "--browser.gatherUsageStats=false",
        "--theme.base=light",
        "--theme.primaryColor=#667eea",
        "--theme.backgroundColor=#ffffff",
        "--theme.secondaryBackgroundColor=#f0f2f6"
    ])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
