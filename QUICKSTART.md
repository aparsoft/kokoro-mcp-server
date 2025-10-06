# Quick Start Guide

Get up and running with Aparsoft TTS in 5 minutes!

## Installation

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install espeak-ng ffmpeg libsndfile1
```

**macOS:**
```bash
brew install espeak ffmpeg
```

### 2. Install Python Package

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install package
pip install -e ".[mcp,cli]"
```

## Quick Examples

### Example 1: Generate Simple Audio

```python
from aparsoft_tts import TTSEngine

engine = TTSEngine()
engine.generate(
    text="Welcome to Aparsoft's YouTube channel",
    output_path="welcome.wav"
)
```

### Example 2: Use the CLI

```bash
# Generate speech
aparsoft-tts generate "Hello world" -o hello.wav

# Use different voice
aparsoft-tts generate "Hello" -v bm_george

# List available voices
aparsoft-tts voices
```

### Example 3: Process a Video Script

```python
from aparsoft_tts import TTSEngine

# Create script file
script = """
Hi, I'm from Aparsoft. In this video, we'll show you
how to deploy AI solutions in just 10 days.

First, let's understand our Quick AI Solutions approach.

Thanks for watching! Subscribe for more.
"""

with open("script.txt", "w") as f:
    f.write(script)

# Generate voiceover
engine = TTSEngine()
engine.process_script("script.txt", "complete_voiceover.wav")
```

### Example 4: Batch Generate Multiple Files

```python
from aparsoft_tts import TTSEngine

engine = TTSEngine()

texts = [
    "Introduction to the video",
    "Main content goes here",
    "Call to action and outro"
]

engine.batch_generate(texts, output_dir="segments/")
```

### Example 5: Custom Configuration

```python
from aparsoft_tts import TTSEngine, TTSConfig

# Configure TTS
config = TTSConfig(
    voice="am_michael",
    speed=1.2,
    enhance_audio=True,
    fade_duration=0.2
)

engine = TTSEngine(config=config)
engine.generate("Custom configuration example", "output.wav")
```

## MCP Server Setup

### Step 1: Find Your Python Path

```bash
# Activate virtual environment first
source /path/to/venv/bin/activate

# Get absolute path
which python  # Linux/macOS
where python  # Windows

# Example output: /home/ram/projects/youtube-creator/venv/bin/python
```

### Step 2: Configure Claude Desktop

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Linux:** `~/.config/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**For Native Linux/macOS:**
```json
{
  "mcpServers": {
    "aparsoft-tts": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["-m", "aparsoft_tts.mcp_server"],
      "env": {
        "LOG_LEVEL": "WARNING"
      }
    }
  }
}
```

**For Windows WSL:**
```json
{
  "mcpServers": {
    "aparsoft-tts": {
      "command": "wsl",
      "args": [
        "-e",
        "/home/ram/projects/youtube-creator/venv/bin/python",
        "-W", "ignore",
        "-m", "aparsoft_tts.mcp_server"
      ],
      "env": {
        "LOG_LEVEL": "WARNING",
        "PYTHONWARNINGS": "ignore"
      }
    }
  }
}
```

### Step 3: Configure Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "aparsoft-tts": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["-m", "aparsoft_tts.mcp_server"]
    }
  }
}
```

### Step 4: Test MCP Server

```bash
# Test server runs correctly
python -m aparsoft_tts.mcp_server --help

# Interactive testing with MCP Inspector
npx @modelcontextprotocol/inspector \
  --command "/path/to/venv/bin/python" \
  --args "-m" "aparsoft_tts.mcp_server"
# Opens at http://localhost:6274
```

### Step 5: Restart Client

- **Claude Desktop:** Completely quit (Cmd/Ctrl+Q) and restart
- **Cursor:** Completely close and reopen

### Step 6: Verify Connection

In Claude/Cursor, ask:
```
"List all available TTS voices using aparsoft-tts tool"

"Generate speech for 'Hello from Aparsoft Kokoro TTS mcp integration' using am_michael voice and save as test.wav"
```

Look for the MCP indicator (🔌) in the chat input area.

## Docker Deployment

```bash
# Build image
docker build -t aparsoft-tts .

# Run server
docker run -v $(pwd)/outputs:/app/outputs aparsoft-tts

# Or use docker-compose
docker-compose up
```

## Environment Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Edit `.env`:
```env
TTS_VOICE=am_michael
TTS_SPEED=1.0
TTS_ENHANCE_AUDIO=true
LOG_LEVEL=INFO
```

## Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=aparsoft_tts
```

## Available Voices

**Male Voices:**
- `am_adam` - American male, natural inflection
- `am_michael` - American male, deeper tones (⭐ recommended)
- `bm_george` - British male, classic accent
- `bm_lewis` - British male, modern accent

**Female Voices:**
- `af_bella` - American female, warm tones
- `af_nicole` - American female, dynamic range
- `af_sarah` - American female, clear articulation
- `af_sky` - American female, youthful energy
- `bf_emma` - British female, professional
- `bf_isabella` - British female, soft tones

**Special:**
- `af` - Default (Bella + Sarah mix)

## Next Steps

- Check out `examples/` for more usage patterns
- Read `CONTRIBUTING.md` to contribute
- Visit https://aparsoft.com for support
- Star the repo if you find it useful!

## Troubleshooting

### System Dependencies

**espeak-ng not found:**
```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng ffmpeg

# macOS
brew install espeak ffmpeg
```

### Audio Issues

**Quality issues:**
```python
engine.generate(text="...", enhance=True)
```

**No audio generated:**
```bash
# Check espeak works
espeak-ng --version

# Test TTS directly
python -c "from aparsoft_tts import TTSEngine; TTSEngine().generate('test', 'test.wav')"
```

### Python/Import Errors

**Import errors:**
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall package
pip install -e ".[mcp,cli]"
```

### MCP Connection Issues

**"Could not attach to MCP server":**
- Use **absolute path** to Python: `/full/path/to/venv/bin/python`
- Test server: `python -m aparsoft_tts.mcp_server`
- Check Python version: `python --version` (needs 3.10+)
- Completely restart Claude/Cursor (not just reload)

**"Tool not found":**
```bash
# Reinstall MCP dependencies
pip install -e ".[mcp]"

# Verify FastMCP
python -c "from fastmcp import FastMCP; print('OK')"
```

**Check Logs:**
```bash
# Claude Desktop
tail -f ~/Library/Logs/Claude/mcp*.log          # macOS
tail -f ~/.config/Claude/logs/mcp*.log          # Linux
type %APPDATA%\Claude\logs\mcp*.log            # Windows
```

## Support

- 📧 Email: contact@aparsoft.com
- 🌐 Website: https://aparsoft.com
- 📖 Full docs: See README.md

---

**Happy Voice Generation! 🎙️**
