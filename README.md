# Kokoro YouTube TTS

A comprehensive Text-to-Speech toolkit built on [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) with audio enhancement, Model Context Protocol (MCP) server integration, CLI interface, and Docker deployment.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## Features

- **Kokoro-82M TTS Engine**: Open-weight model with 82M parameters (510 tokens per pass)
- **Audio Enhancement**: Professional processing with librosa (normalization, noise reduction, fade in/out)
- **MCP Server**: Model Context Protocol integration for Claude Desktop, Cursor, and other AI tools
- **CLI Interface**: Command-line tools for quick generation
- **Batch Processing**: Generate multiple audio files efficiently
- **Script Processing**: Convert complete video scripts with automatic text chunking
- **Docker Support**: Containerization with docker-compose
- **Enterprise Features**: Structured logging, configuration management, comprehensive testing
- **CI/CD**: GitHub Actions pipeline with automated testing

---

## Building on Kokoro-82M

We integrate Kokoro-82M's excellent TTS inference with development tooling and workflow enhancements. This toolkit adds:

1. **Audio post-processing** - Normalization, noise reduction, silence trimming, and fade in/out using librosa
2. **Automated script workflows** - Direct script-to-voiceover conversion with paragraph detection and gap management
3. **IDE-native generation** - MCP server integration eliminates context switching for Claude Desktop and Cursor users
4. **Deployment infrastructure** - Docker deployment, structured logging, configuration management, and comprehensive testing
5. **Batch processing** - CLI and Python APIs for processing multiple segments efficiently

### Technical Implementation

**Audio Enhancement (librosa Integration):**

This toolkit adds an audio processing pipeline on Kokoro generated TTS output:

```python
# Without enhancement - raw Kokoro output
audio = kokoro_pipeline(text)

# With enhancement
audio = enhance_audio(
    kokoro_output,
    normalize=True,        # Consistent volume
    trim_silence=True,     # Remove dead air
    noise_reduction=True,  # Spectral gating
    add_fade=True         # Smooth transitions
)
```

**Result:** Voiceovers ready for YouTube, podcasts, or content creation without additional audio editing.

**MCP Server Integration:**

Traditional workflow:
```bash
# 1. Write script in Claude/Cursor
# 2. Copy text to terminal
# 3. Run Python script
# 4. Switch back to editor
# 5. Repeat for each segment
```

With MCP server:
```bash
# In Claude Desktop or Cursor:
"Generate voiceover for this section using am_michael voice"
# Done. Audio generated without leaving your workspace.
```

**Workflow Enhancement:**

- **Content creators**: Write scripts in AI editors, generate voiceovers inline
- **Developers**: Generate test audio during development without context switching
- **Teams**: Standardized TTS across tools (Claude, Cursor, CLI, API)
- **Automation**: AI agents can generate audio as part of content pipelines

**Deployment Features:**

The toolkit wraps Kokoro with common deployment and development needs:

- **Configuration management** - Environment-based settings, no hardcoded values
- **Structured logging** - JSON logs for aggregation, correlation IDs for tracing
- **Error handling** - Custom exceptions, graceful failures, detailed error context
- **Testing** - Comprehensive test suite, CI/CD integration
- **Docker deployment** - Containerized with health checks, resource limits
- **CLI interface** - Quick access without writing code

### Use Cases

**YouTube/Podcast Production:**
```python
# Process entire video script with proper gaps
engine.process_script("script.txt", "voiceover.wav", gap_duration=0.5)
```

**AI-Assisted Content Creation:**
```
# In Claude Desktop with MCP:
User: "Generate a 30-second intro for my coding tutorial"
Claude: *generates script and voiceover via MCP*
```

**Batch Content Generation:**
```python
# Generate 100 audio segments for e-learning course
engine.batch_generate(lesson_texts, output_dir="lessons/")
```

**Development/Testing:**
```bash
# Quick CLI test during development
aparsoft-tts generate "Test message" -o test.wav
```

---

## Quick Start

### Installation

**System Dependencies:**

```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng ffmpeg libsndfile1

# macOS
brew install espeak ffmpeg

# Windows: Download from
# - espeak-ng: http://espeak.sourceforge.net/
# - ffmpeg: https://ffmpeg.org/download.html
```

**Python Package:**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install with all features
pip install -e ".[mcp,cli]"
```

### Basic Usage

```python
from aparsoft_tts import TTSEngine

# Initialize engine
engine = TTSEngine()

# Generate speech
engine.generate(
    text="Welcome to Kokoro YouTube TTS",
    output_path="output.wav"
)
```

### CLI Usage

```bash
# Generate audio
aparsoft-tts generate "Hello world" -o output.wav

# List available voices
aparsoft-tts voices

# Process video script
aparsoft-tts script video_script.txt -o voiceover.wav

# Batch generate
aparsoft-tts batch "Intro" "Body" "Outro" -d segments/
```

---

## Available Voices

**Male Voices:**
- `am_adam` - American male (natural inflection)
- `am_michael` - American male (deeper tones, professional)
- `bm_george` - British male (classic accent)
- `bm_lewis` - British male (modern accent)

**Female Voices:**
- `af_bella` - American female (warm tones)
- `af_nicole` - American female (dynamic range)
- `af_sarah` - American female (clear articulation)
- `af_sky` - American female (youthful energy)
- `bf_emma` - British female (professional)
- `bf_isabella` - British female (soft tones)

**Special Voices:**
- `af` - Default mix (50-50 blend of Bella and Sarah)

---

## Advanced Usage

### Custom Configuration

```python
from aparsoft_tts import TTSEngine, TTSConfig

# Create custom configuration
config = TTSConfig(
    voice="bm_george",
    speed=1.2,
    enhance_audio=True,
    fade_duration=0.2
)

engine = TTSEngine(config=config)
engine.generate("Custom configuration", "output.wav")
```

### Audio Enhancement

```python
from aparsoft_tts.utils.audio import enhance_audio

# Generate raw audio
audio = engine.generate("Test audio")

# Apply custom enhancement
enhanced = enhance_audio(
    audio,
    sample_rate=24000,
    normalize=True,
    trim_silence=True,
    trim_db=25.0,
    noise_reduction=True,
    add_fade=True,
    fade_duration=0.15
)
```

### Batch Processing

```python
# Process multiple texts
texts = [
    "Welcome to the tutorial",
    "Let's explore the features",
    "Thanks for watching"
]

paths = engine.batch_generate(
    texts=texts,
    output_dir="segments/",
    voice="am_michael"
)
```

### Script Processing

```python
# Process complete video script with automatic text chunking
engine.process_script(
    script_path="video_script.txt",
    output_path="complete_voiceover.wav",
    gap_duration=0.5,  # Gap between paragraphs
    voice="am_michael",
    speed=1.0
)

# Note: Kokoro processes up to 510 tokens per pass.
# Long scripts are automatically chunked and combined seamlessly.
```

### Streaming Generation

```python
# Generate audio in chunks
for chunk in engine.generate_stream(
    text="Long text for streaming...",
    voice="am_michael"
):
    # Process chunk as it's generated
    process_audio_chunk(chunk)
```

---

## Model Context Protocol (MCP) Integration

### Quick MCP Setup (5 Minutes)

**What is MCP?** Model Context Protocol lets Claude Desktop and Cursor generate speech directly from your conversations. No copy-pasting, no context switching.

#### For Developers: Quick Start

```bash
# 1. Find your Python path
which python  # Linux/Mac
where python  # Windows

# Example output: /home/ram/projects/youtube-creator/venv/bin/python
```

**Claude Desktop:**

```bash
# 1. Open config (creates if doesn't exist)
code ~/Library/Application\ Support/Claude/claude_desktop_config.json  # macOS
code ~/.config/Claude/claude_desktop_config.json  # Linux
notepad %APPDATA%\Claude\claude_desktop_config.json  # Windows

# 2. Add this (use YOUR absolute Python path):
{
  "mcpServers": {
    "aparsoft-tts": {
      "command": "/absolute/path/to/your/venv/bin/python",
      "args": ["-m", "aparsoft_tts.mcp_server"]
    }
  }
}

# 3. Restart Claude (Cmd/Ctrl + R)
```

**Cursor:**

```bash
# 1. Create/edit config
mkdir -p ~/.cursor && code ~/.cursor/mcp.json

# 2. Add this (use YOUR absolute Python path):
{
  "mcpServers": {
    "aparsoft-tts": {
      "command": "/absolute/path/to/your/venv/bin/python",
      "args": ["-m", "aparsoft_tts.mcp_server"]
    }
  }
}

# 3. Restart Cursor completely
```

#### Testing MCP Server

```bash
# Quick test - should print server info
python -m aparsoft_tts.mcp_server --help

# Interactive testing with MCP Inspector
npx @modelcontextprotocol/inspector \
  --command "/path/to/venv/bin/python" \
  --args "-m" "aparsoft_tts.mcp_server"
# Opens UI at http://localhost:6274
```

#### Usage Examples

In Claude Desktop or Cursor, just ask naturally:

```
# Basic generation
"Generate speech for 'Welcome to my channel' using am_michael voice"

# Voice discovery
"List all available TTS voices"

# Batch processing
"Create voiceovers for these three segments: 'Intro', 'Main', 'Outro'"

# Script processing
"Process video_script.txt and create a complete voiceover"

# Custom parameters
"Generate 'Test message' at 1.3x speed with British accent"
```

### MCP Tools Available

1. **generate_speech**: Single audio generation with full control
   - Text input (up to 10,000 characters)
   - Voice selection (6 voices)
   - Speed control (0.5x - 2.0x)
   - Audio enhancement toggle

2. **list_voices**: Get voice catalog with descriptions

3. **batch_generate**: Process multiple texts efficiently

4. **process_script**: Complete video script conversion
   - Automatic paragraph detection
   - Configurable gap duration
   - Handles long texts via automatic chunking

### Troubleshooting MCP

**"Could not attach to MCP server"**
- Use absolute path: `/full/path/to/venv/bin/python`
- Test server runs: `python -m aparsoft_tts.mcp_server`
- Check Python version: `python --version` (needs 3.10+)

**"Tool not found"**
```bash
# Reinstall MCP dependencies
pip install -e ".[mcp]"

# Verify FastMCP
python -c "from fastmcp import FastMCP; print('✅ OK')"
```

**Detailed Documentation:** See [TUTORIAL.md](local_folder/TUTORIAL.md) for comprehensive MCP guide with advanced features, debugging, and production deployment.

---

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t aparsoft-tts:latest .

# Run MCP server
docker run -d \
  --name aparsoft-tts \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/logs:/app/logs \
  aparsoft-tts:latest

# Run CLI commands
docker run --rm \
  -v $(pwd)/outputs:/app/outputs \
  aparsoft-tts:latest \
  aparsoft-tts generate "Docker test" -o /app/outputs/test.wav
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Variables

```bash
# TTS Configuration
TTS_VOICE=am_michael
TTS_SPEED=1.0
TTS_ENHANCE_AUDIO=true

# MCP Server
MCP_SERVER_NAME=aparsoft-tts-server
MCP_ENABLE_RATE_LIMITING=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## Project Structure

```
youtube-creator/
├── aparsoft_tts/
│   ├── core/
│   │   └── engine.py          # TTS engine
│   ├── utils/
│   │   ├── audio.py           # Audio processing with librosa
│   │   ├── logging.py         # Structured logging
│   │   └── exceptions.py      # Custom exceptions
│   ├── config.py              # Configuration management
│   ├── cli.py                 # CLI interface
│   └── mcp_server.py          # MCP server (FastMCP)
├── tests/
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── examples/                  # Usage examples
├── pyproject.toml             # Project metadata
├── Dockerfile                 # Docker configuration
└── docker-compose.yml         # Docker Compose config
```

---

## Audio Processing

The toolkit enhances Kokoro's output with professional audio processing:

**Features:**
- Normalization: Consistent volume levels
- Silence Trimming: Remove quiet sections (configurable threshold)
- Noise Reduction: Spectral gating for cleaner audio
- Fade In/Out: Smooth transitions, prevents clicks
- Custom Processing: Extensible with librosa/scipy

**Enhancement Pipeline:**

```python
from aparsoft_tts.utils.audio import enhance_audio, save_audio

# Generate raw audio
audio = engine.generate("Your text here")

# Apply enhancement pipeline
enhanced = enhance_audio(
    audio,
    sample_rate=24000,
    normalize=True,      # Normalize volume
    trim_silence=True,   # Trim silence
    trim_db=20.0,        # Threshold in dB
    noise_reduction=True,  # Apply noise gate
    add_fade=True,       # Add fade in/out
    fade_duration=0.1    # 100ms fade
)

# Save enhanced audio
save_audio(enhanced, "enhanced.wav", sample_rate=24000)
```

---

## Configuration

### Using Configuration Files

```python
from aparsoft_tts import TTSConfig, MCPConfig, LoggingConfig, Config

# TTS settings
tts_config = TTSConfig(
    voice="am_michael",
    speed=1.0,
    enhance_audio=True,
    sample_rate=24000,
    output_format="wav"
)

# MCP server settings
mcp_config = MCPConfig(
    server_name="aparsoft-tts-production",
    enable_rate_limiting=True,
    rate_limit_calls=100
)

# Logging settings
logging_config = LoggingConfig(
    level="INFO",
    format="json",
    output="file"
)

# Combined configuration
config = Config(
    tts=tts_config,
    mcp=mcp_config,
    logging=logging_config
)
```

### Environment Variables

Create `.env` file:

```env
# TTS Settings
TTS_VOICE=am_michael
TTS_SPEED=1.0
TTS_ENHANCE_AUDIO=true
TTS_SAMPLE_RATE=24000

# Audio Processing
TTS_TRIM_SILENCE=true
TTS_TRIM_DB=20.0
TTS_FADE_DURATION=0.1

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=console
LOG_OUTPUT=stdout
```

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aparsoft_tts --cov-report=html

# Run specific test file
pytest tests/unit/test_engine.py

# Run only fast tests
pytest -m "not slow"
```

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/aparsoft/kokoro-youtube-tts.git
cd kokoro-youtube-tts

# Install with dev dependencies
pip install -e ".[dev,mcp,cli,all]"

# Install pre-commit hooks
pre-commit install
```

### Running CI Locally

The project includes GitHub Actions workflow for CI/CD:
- Code quality checks (Black, Ruff, mypy)
- Tests on multiple Python versions (3.10, 3.11, 3.12)
- Docker build verification
- Security scanning with Trivy

---

## API Reference

### TTSEngine

**Initialization:**
```python
TTSEngine(config: TTSConfig | None = None)
```

**Methods:**

- `generate(text, output_path, voice, speed, enhance)` - Generate speech
- `generate_stream(text, voice, speed)` - Stream audio chunks
- `batch_generate(texts, output_dir, voice, speed)` - Batch processing
- `process_script(script_path, output_path, gap_duration, voice, speed)` - Process scripts
- `list_voices()` - Get available voices

### Configuration Classes

- `TTSConfig` - TTS engine settings
- `MCPConfig` - MCP server configuration
- `LoggingConfig` - Logging configuration
- `Config` - Main application configuration

### Audio Utilities

- `enhance_audio(audio, ...)` - Apply audio enhancement
- `combine_audio_segments(segments, ...)` - Combine audio files
- `save_audio(audio, path, ...)` - Save audio to file
- `load_audio(path, ...)` - Load audio from file
- `chunk_audio(audio, ...)` - Split audio into chunks
- `get_audio_duration(audio, ...)` - Get audio duration

---

## Examples

See the `examples/` directory for complete examples:

- `basic_usage.py` - Simple generation examples
- `youtube_workflow.py` - Complete YouTube video production workflow

---

## Troubleshooting

### espeak-ng not found

```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng

# macOS
brew install espeak

# Windows: Download from http://espeak.sourceforge.net/
```

### Audio quality issues

Enable audio enhancement:
```python
engine.generate(text="Your text", enhance=True)
```

### Import errors

Ensure virtual environment is activated:
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### Docker issues

Check container logs:
```bash
docker logs aparsoft-tts
```

---

## Performance

**Benchmarks** (on typical consumer hardware):

- Model Loading: ~2-3 seconds (one-time)
- Generation Speed: ~0.5s per second of audio
- Memory Usage: ~2GB RAM (model loaded)
- Token Processing: Up to 510 tokens per pass

**Text Length Limits:**

Kokoro-82M processes up to 510 tokens in a single pass. For longer texts:
- Automatic chunking: Engine automatically splits long texts
- Script processing: Handles unlimited length via intelligent segmentation
- Batch processing: Each segment processed independently

**Optimization Tips:**

1. Reuse engine instances (avoid reloading model)
2. Disable enhancement for draft generations (`enhance=False`)
3. Use streaming for long texts (automatic chunking)
4. Batch process multiple files for efficiency
5. Enable GPU acceleration on supported platforms
6. For very long texts, use `process_script()` for optimal chunking

---

## Credits & Acknowledgements

This project builds upon excellent open-source software:

### Core Dependencies

- **[Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)** by hexgrad - Apache License 2.0
  - Open-weight TTS model with 82M parameters
  - Processes up to 510 tokens per pass
  - Architectured by @yl4579 (StyleTTS 2)
  - 24kHz audio output, <100 hours training data

- **[librosa](https://librosa.org/)** - ISC License
  - Audio analysis and processing

- **[FastMCP](https://github.com/jlowin/fastmcp)** - MIT License
  - Model Context Protocol server framework

### Additional Dependencies

- **soundfile** - Audio I/O
- **pydantic** - Configuration management
- **structlog** - Structured logging
- **typer** - CLI framework
- **pytest** - Testing framework

### Special Thanks

- 🛠️ @yl4579 for StyleTTS 2 architecture
- 🏆 hexgrad team for Kokoro model and inference library
- 🌐 Anthropic for Model Context Protocol
- 📊 All contributors to the open-source dependencies

---

## License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

**Third-Party Licenses:**
- Kokoro-82M: Apache License 2.0
- librosa: ISC License
- FastMCP: MIT License

---

## Support

- **Email**: contact@aparsoft.com
- **Phone**: +91 8904064878
- **Website**: https://aparsoft.com
- **Issues**: [GitHub Issues](https://github.com/aparsoft/kokoro-youtube-tts/issues)

---

## Citation

If you use this toolkit in your research or project, please cite:

```bibtex
@software{kokoro_youtube_tts,
  author = {Aparsoft},
  title = {Kokoro YouTube TTS: Comprehensive TTS Toolkit},
  year = {2025},
  url = {https://github.com/aparsoft/kokoro-youtube-tts}
}
```

For the Kokoro model:

```bibtex
@software{kokoro_tts,
  author = {hexgrad},
  title = {Kokoro-82M: Open-weight TTS Model},
  year = {2024},
  url = {https://huggingface.co/hexgrad/Kokoro-82M}
}
```

---

**Built with ❤️ for the video creator community**
