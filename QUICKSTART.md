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

### For Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "aparsoft-tts": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "aparsoft_tts.mcp_server"]
    }
  }
}
```

### For Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "aparsoft-tts": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "aparsoft_tts.mcp_server"]
    }
  }
}
```

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
- `am_michael` - Professional American male (⭐ recommended)
- `bm_george` - British male, formal
- `am_adam` - American male, younger

**Female Voices:**
- `af_bella` - American female, warm
- `af_heart` - American female, expressive
- `bf_emma` - British female, professional

## Next Steps

- Check out `examples/` for more usage patterns
- Read `CONTRIBUTING.md` to contribute
- Visit https://aparsoft.com for support
- Star the repo if you find it useful!

## Troubleshooting

### espeak-ng not found
```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng

# macOS
brew install espeak
```

### Audio quality issues
Enable audio enhancement:
```python
engine.generate(text="...", enhance=True)
```

### Import errors
Make sure you're in the virtual environment:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

## Support

- 📧 Email: contact@aparsoft.com
- 📞 Phone: +91 8904064878
- 🌐 Website: https://aparsoft.com
- 📖 Full docs: See README.md

---

**Happy Voice Generation! 🎙️**
