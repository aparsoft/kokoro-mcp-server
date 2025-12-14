# Aparsoft TTS MCP Server - Usage Guide

## Quick Start

The MCP server is now available as a clean package with FastMCP 2.x patterns.

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
from aparsoft_tts.mcp_server import mcp, main, config, get_tts_engine

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

### Tools (7 available) - FastMCP 2.x with Context
| Tool | Description | Key Features |
|------|-------------|--------------|
| `generate_speech` | Convert text to speech | Progress reporting, client logging |
| `list_voices` | Get available voices (14 total) | `readOnlyHint=True` annotation |
| `batch_generate` | Process multiple texts | Parallel generation, progress |
| `process_script` | Convert plain text scripts | File-based processing |
| `process_educational_script` | 🎓 Markdown scripts with segments | Auto-parses `## SEGMENT` |
| `generate_podcast` | Create multi-voice podcasts | Variable speeds, gaps |
| `transcribe_speech` | Audio to text (Whisper) | STT integration |

### Resources (4 available) - With Tags and MIME Types
| Resource | Description | MIME Type |
|----------|-------------|-----------|
| `tts://voice/info/{voice_id}` | Voice details (template) | `application/json` |
| `tts://voices/comparison` | Compare all voices | `application/json` |
| `tts://presets/{preset_name}` | Preset settings (template) | `application/json` |
| `tts://presets/all` | All presets | `application/json` |

### Prompts (6 available) - With Descriptions and Tags
| Prompt | Description | Tags |
|--------|-------------|------|
| `podcast_creator` | Podcast creation guide with AI disclosure | `podcast, workflow` |
| `voice_selector` | Voice selection helper | `voice, selection` |
| `script_optimizer` | Script optimization tips | `script, best-practices` |
| `hindi_script_optimizer` | Hindi-specific TTS optimization | `hindi, kokoro` |
| `educational_script_processor` | 🎓 Educational script guide | `educational, markdown` |
| `troubleshoot_tts` | Troubleshooting guide | `troubleshooting, quality` |

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
├── __init__.py              # Main entry point, exports mcp instance
├── __main__.py              # Module execution entry (python -m)
├── mcp_server_main.py       # Core setup, Pydantic models, MCP instance
├── mcp_tools.py             # Tool implementations (with Context)
├── mcp_tools_educational.py # Educational script tool
├── mcp_resources.py         # Resource implementations (with tags)
├── mcp_prompts.py           # Prompt implementations (with tags)
└── mcp_utils.py             # Shared utilities
```

## FastMCP 2.x Features

### Context Injection

All tools now receive a `Context` object for client-visible logging and progress:

```python
from mcp.server.fastmcp import Context

@mcp.tool(...)
async def my_tool(request: MyRequest, ctx: Context) -> str:
    # Client-visible logging
    await ctx.info("Processing request...")
    await ctx.warning("This might take a while")
    await ctx.error("Something went wrong")
    
    # Progress reporting
    await ctx.report_progress(progress=0.5, total=1.0)
    
    return result
```

### ToolAnnotations

Tools can declare semantic hints for MCP clients:

```python
from mcp.types import ToolAnnotations

@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,    # Doesn't modify state
        idempotentHint=True,  # Safe to retry
        destructiveHint=False # Doesn't delete data
    )
)
```

### Tags

Tools, resources, and prompts can be tagged for categorization:

```python
@mcp.tool(
    tags={"tts", "audio", "generation"}
)
async def generate_speech(...):
    ...
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
- Tools: 7 (6 main + 1 educational)
- Resources: 4 (2 static + 2 templates)
- Prompts: 6

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
- FastMCP 2.x handles automatic schema generation from type hints
- Context logging is visible in MCP clients that support it
- Progress reporting provides real-time feedback during long operations
- Tags help clients organize and discover tools/resources/prompts

## Migration from FastMCP 1.x

If you were using an older version, here are the key changes:

| Old Pattern | New FastMCP 2.x Pattern |
|-------------|-------------------------|
| `@mcp.tool()` | `@mcp.tool(annotations=..., tags=...)` |
| No Context | `async def tool(request, ctx: Context)` |
| No progress | `await ctx.report_progress(...)` |
| Server logging only | `await ctx.info(...)` client logging |
| No semantic hints | `ToolAnnotations(readOnlyHint=...)` |
