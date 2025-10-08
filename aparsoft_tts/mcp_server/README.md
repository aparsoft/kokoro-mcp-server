# Aparsoft TTS MCP Server

FastMCP-based Model Context Protocol server for Aparsoft TTS.

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Run the MCP server
python -m aparsoft_tts.mcp_server
```

## Architecture

### Single Instance Pattern ✅

All modules use **one shared MCP instance** from `mcp_server_main.py`:

```python
# All modules import the SAME instance
from aparsoft_tts.mcp_server import mcp, main, config, tts_engine
```

### Module Structure

```
aparsoft_tts/mcp_server/
├── __init__.py          # 📦 Main entry point (import from here!)
├── __main__.py          # 🚀 Module execution entry
├── mcp_server_main.py   # ⚙️  Core setup, single MCP instance
├── mcp_tools.py         # 🔧 6 tool implementations
├── mcp_resources.py     # 📚 4 resource implementations
├── mcp_prompts.py       # 💡 4 prompt implementations
└── mcp_utils.py         # 🛠️  Shared utilities
```

## Components

### 🔧 Tools (6)
- `generate_speech` - Text to speech conversion
- `list_voices` - Available voices
- `batch_generate` - Batch processing
- `process_script` - Script file processing
- `generate_podcast` - Multi-voice podcasts
- `transcribe_speech` - Audio to text

### 📚 Resources (4)
- `tts://voice/info/{voice_id}` - Voice details _(template)_
- `tts://voices/comparison` - Voice comparison _(static)_
- `tts://presets/{preset_name}` - Preset configs _(template)_
- `tts://presets/all` - All presets _(static)_

### 💡 Prompts (4)
- `podcast_creator` - Podcast creation guide
- `voice_selector` - Voice selection helper
- `script_optimizer` - Script optimization
- `troubleshoot_tts` - Troubleshooting guide

## Configuration

### Claude Desktop

Edit `~/.config/Claude/claude_desktop_config.json`:

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

### Cursor

Edit `~/.cursor/mcp.json`:

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

## Usage in Code

```python
# Import the main components
from aparsoft_tts.mcp_server import (
    mcp,           # FastMCP server instance
    main,          # Entry point function
    config,        # Configuration object
    tts_engine,    # TTS engine instance
)

# Import Pydantic models for type hints
from aparsoft_tts.mcp_server import (
    GenerateSpeechRequest,
    BatchGenerateRequest,
    ProcessScriptRequest,
    GeneratePodcastRequest,
    PodcastSegment,
    TranscribeAudioRequest,
)

# All modules share the SAME mcp instance
print(f"Server: {mcp.name}")  # aparsoft-tts-server
```

## Verification

Test the server:

```bash
# Check syntax
python -m py_compile aparsoft_tts/mcp_server/*.py

# Test imports
python -c "from aparsoft_tts.mcp_server import mcp; print(f'✅ {mcp.name}')"

# Run server (Ctrl+C to stop)
python -m aparsoft_tts.mcp_server
```

## Debugging

Enable debug logging:

```bash
LOG_LEVEL=DEBUG python -m aparsoft_tts.mcp_server
```

Use MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

## Key Features

✅ **Single MCP Instance** - No duplicates, consistent state  
✅ **Clean Imports** - Import from package level  
✅ **Type Safety** - Pydantic models with validation  
✅ **FastMCP** - Automatic schema generation  
✅ **Production Ready** - Comprehensive error handling  

## Documentation

- [USAGE.md](./USAGE.md) - Detailed usage guide
- [FastMCP Docs](https://gofastmcp.com/) - FastMCP documentation
- [MCP Spec](https://modelcontextprotocol.io/) - Model Context Protocol

## Testing

All tests pass ✅:
- Single instance verification
- Component registration
- Pydantic model validation
- Module execution
- Import structure
- Configuration loading

---

**Status**: ✅ Production Ready  
**Framework**: FastMCP v2  
**Protocol**: Model Context Protocol (MCP)  
**Transport**: stdio
