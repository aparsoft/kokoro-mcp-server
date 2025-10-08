# Aparsoft TTS MCP Server - Usage Guide

## Quick Start

The MCP server is now available as a clean package with a single shared instance.

### Running the Server

```bash
# Activate your virtual environment
source venv/bin/activate

# Run the MCP server
python -m aparsoft_tts.mcp_server
```

### Importing in Code

```python
# Import the main MCP instance and entry point
from aparsoft_tts.mcp_server import mcp, main, config, tts_engine

# Import Pydantic models for type hints
from aparsoft_tts.mcp_server import (
    GenerateSpeechRequest,
    BatchGenerateRequest,
    ProcessScriptRequest,
    GeneratePodcastRequest,
    PodcastSegment,
    TranscribeAudioRequest,
)
```

## Configuration for MCP Clients

### Claude Desktop

Edit `~/.config/Claude/claude_desktop_config.json` (Linux) or  
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

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

## Server Components

### Tools (6 available)
- `generate_speech` - Convert text to speech
- `list_voices` - Get available voices
- `batch_generate` - Process multiple texts
- `process_script` - Convert script files
- `generate_podcast` - Create multi-voice podcasts
- `transcribe_speech` - Audio to text

### Resources (4 available)
- `tts://voice/info/{voice_id}` - Voice details (template)
- `tts://voices/comparison` - Compare all voices (static)
- `tts://presets/{preset_name}` - Preset settings (template)
- `tts://presets/all` - All presets (static)

### Prompts (4 available)
- `podcast_creator` - Podcast creation guide
- `voice_selector` - Voice selection helper
- `script_optimizer` - Script optimization tips
- `troubleshoot_tts` - Troubleshooting guide

## Architecture

### Single Instance Pattern

All modules (`mcp_tools.py`, `mcp_resources.py`, `mcp_prompts.py`) import and use the **same** MCP server instance from `mcp_server_main.py`. This ensures:

- No duplicate registrations
- Consistent state across modules
- Clean import structure
- Single source of truth

### Module Structure

```
aparsoft_tts/mcp_server/
├── __init__.py          # Main entry point, exports mcp instance
├── __main__.py          # Module execution entry (python -m)
├── mcp_server_main.py   # Core setup, Pydantic models, MCP instance
├── mcp_tools.py         # Tool implementations
├── mcp_resources.py     # Resource implementations
├── mcp_prompts.py       # Prompt implementations
└── mcp_utils.py         # Shared utilities
```

## Verification

Test the server setup:

```python
from aparsoft_tts.mcp_server import mcp

# Check registered components
print(f"Tools: {len(mcp._tool_manager._tools)}")
print(f"Resources: {len(mcp._resource_manager._resources) + len(mcp._resource_manager._templates)}")
print(f"Prompts: {len(mcp._prompt_manager._prompts)}")
```

Expected output:
- Tools: 6
- Resources: 4 (2 static + 2 templates)
- Prompts: 4

## Debugging

Enable debug logging:

```bash
LOG_LEVEL=DEBUG python -m aparsoft_tts.mcp_server
```

Check logs:
- Claude Desktop: Check the client's log directory
- Use MCP Inspector: `npx @modelcontextprotocol/inspector`

## Notes

- The server uses stdio transport by default (required for Claude Desktop/Cursor)
- All logging goes to stderr to avoid interfering with MCP protocol
- Pydantic models ensure type safety and validation
- FastMCP handles automatic schema generation from type hints
