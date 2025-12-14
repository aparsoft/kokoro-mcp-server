# Aparsoft TTS MCP Server

FastMCP 2.x-based Model Context Protocol server for Aparsoft TTS.

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
from aparsoft_tts.mcp_server import mcp, main, config, get_tts_engine
```

### FastMCP 2.x Features ✨

This server leverages FastMCP 2.x patterns:

| Feature | Description |
|---------|-------------|
| **Context Injection** | All tools receive `Context` for client-visible logging and progress |
| **ToolAnnotations** | Semantic hints like `readOnlyHint`, `idempotentHint` for tools |
| **Tags** | Tool/resource/prompt categorization for better discoverability |
| **Progress Reporting** | Real-time progress via `ctx.report_progress()` |
| **Client Logging** | Client-visible logs via `ctx.info()`, `ctx.error()` |
| **Duplicate Handling** | `on_duplicate_tools="warn"` for safe component registration |

### Module Structure

```
aparsoft_tts/mcp_server/
├── __init__.py               # 📦 Main entry point (import from here!)
├── __main__.py               # 🚀 Module execution entry
├── mcp_server_main.py        # ⚙️  Core setup, single MCP instance
├── mcp_tools.py              # 🔧 7 tool implementations (with Context)
├── mcp_tools_educational.py  # 🎓 Educational script tool
├── mcp_resources.py          # 📚 4 resource implementations (with tags/mime_type)
├── mcp_prompts.py            # 💡 6 prompt implementations (with tags)
└── mcp_utils.py              # 🛠️  Shared utilities
```

## Components

### 🔧 Tools (7) - All with FastMCP 2.x Context Support
| Tool | Description | Annotations |
|------|-------------|-------------|
| `generate_speech` | Text to speech conversion | `readOnlyHint=False` |
| `list_voices` | Available voices (14 total: 10 English + 4 Hindi) | `readOnlyHint=True` |
| `batch_generate` | Batch processing | `readOnlyHint=False` |
| `process_script` | Plain text script processing | `readOnlyHint=False` |
| `process_educational_script` | 🎓 Educational scripts with segments/speeds | `readOnlyHint=False` |
| `generate_podcast` | Multi-voice podcasts | `readOnlyHint=False` |
| `transcribe_speech` | Audio to text (OpenAI Whisper) | `readOnlyHint=False, idempotentHint=True` |

### 📚 Resources (4) - With Tags and MIME Types
| Resource URI | Description | Tags |
|--------------|-------------|------|
| `tts://voice/info/{voice_id}` | Voice details (includes Hindi) | `voice, info, kokoro` |
| `tts://voices/comparison` | Voice comparison by quality tier | `voice, comparison, selection` |
| `tts://presets/{preset_name}` | Preset configs (includes Hindi) | `preset, config, use-case` |
| `tts://presets/all` | All presets by category | `preset, catalog, all` |

### 💡 Prompts (6) - With Descriptions and Tags
| Prompt | Description | Tags |
|--------|-------------|------|
| `podcast_creator` | Podcast creation guide with AI disclosure | `podcast, creation, workflow` |
| `voice_selector` | Voice selection helper | `voice, selection, recommendation` |
| `script_optimizer` | Script optimization for TTS | `script, optimization, best-practices` |
| `hindi_script_optimizer` | Hindi-specific TTS optimization | `hindi, script, kokoro, indic` |
| `educational_script_processor` | 🎓 Educational script guide | `educational, script, tutorial` |
| `troubleshoot_tts` | Troubleshooting guide | `troubleshooting, debug, quality` |

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
    mcp,              # FastMCP server instance
    main,             # Entry point function
    config,           # Configuration object
    get_tts_engine,   # Lazy TTS engine loader
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

### FastMCP 2.x Tool Pattern

```python
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

@mcp.tool(
    name="my_tool",
    description="What this tool does",
    annotations=ToolAnnotations(
        readOnlyHint=False,      # Creates/modifies files
        idempotentHint=True,     # Safe to retry
    ),
    tags={"tts", "audio"},       # Categorization
)
async def my_tool(request: MyRequest, ctx: Context) -> str:
    """Tool implementation with Context support."""
    await ctx.info("Starting operation...")
    await ctx.report_progress(progress=0.5, total=1.0)
    
    try:
        # ... do work ...
        return "Success!"
    except Exception as e:
        await ctx.error(f"Failed: {e}")
        raise
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
✅ **Hindi Support** - 4 Hindi voices (hf_alpha, hf_beta, hm_omega, hm_psi)  
✅ **Educational Scripts** - Dedicated tool for markdown scripts with segments

---

## 🚨 CRITICAL: Tool Selection Guide

### ⚠️ Common Mistake: Using Wrong Tool!

**Problem:** Educational scripts processed with wrong tool → Voice reads "hash hash hash"!

### ✅ Decision Tree

**BEFORE processing ANY script, ask:**

#### Q1: Is this a markdown file with `## SEGMENT` headers?
- **YES** → Go to Q2
- **NO** → Go to Q3

#### Q2: Does it have variable speeds like `[Speed: 1.2x]`?
- **YES** → Use **`process_educational_script`** ✅
- **NO** → Extract text manually → Use `generate_podcast`

#### Q3: Is it plain text (no markdown)?
- **YES** → Use `process_script` ✅
- **NO** → Extract text first, then choose tool

### 📋 Quick Reference

| Script Type | Format | Tool to Use |
|-------------|--------|-------------|
| Educational tutorial with segments | Markdown `## SEGMENT [Speed: X.Xx]` | `process_educational_script` |
| Plain text script | `.txt` no formatting | `process_script` |
| Multiple separate texts | Multiple strings | `batch_generate` |
| Single short text | Single string | `generate_speech` |
| Podcast with multiple voices | Manual segments array | `generate_podcast` |

### 🎓 Educational Script Example

**INPUT (tutorial.md):**
```markdown
## SEGMENT 1 - Introduction [Speed: 1.2x]
Welcome to our tutorial!

## SEGMENT 2 - Main Content [Speed: 1.1x]
Let's learn something new.
```

**CORRECT APPROACH:**
```python
await process_educational_script(ProcessEducationalScriptRequest(
    script_path="tutorial.md",
    voice="hf_beta",  # Hindi female
    output_path="output.wav"
))
```

**Result:** ✅ Clean narration with proper speeds!

**WRONG APPROACH:**
```python
# ❌ DON'T DO THIS!
await process_script(ProcessScriptRequest(
    script_path="tutorial.md"
))
```

**Result:** ❌ Voice reads "hash hash SEGMENT 1 dash Introduction bracket Speed..."

---

## 🇮🇳 Hindi Voice Support

### Available Hindi Voices

**Female:**
- `hf_alpha` - General use, clear pronunciation
- `hf_beta` - Expressive, storytelling

**Male:**
- `hm_omega` - Professional, authoritative
- `hm_psi` - Conversational, friendly

### Prerequisites

```bash
# Install espeak-ng for Hindi support
sudo apt-get install espeak-ng

# Verify Hindi support
espeak-ng -v hi "नमस्ते" --stdout > test.wav
```

### Usage

```python
# Generate Hindi speech
await generate_speech(GenerateSpeechRequest(
    text="नमस्ते, आपका स्वागत है",
    voice="hf_alpha",
    output_file="hindi_hello.wav"
))

# Hindi podcast
await generate_podcast(GeneratePodcastRequest(
    segments=[
        PodcastSegment(
            text="आज हम एक महत्वपूर्ण विषय पर चर्चा करेंगे",
            voice="hf_alpha",
            speed=1.0
        ),
        PodcastSegment(
            text="यह बहुत रोचक होगा",
            voice="hm_omega",
            speed=1.1
        )
    ]
))
```

### Hindi Presets

- `hindi_tutorial` - Educational content
- `hindi_podcast` - Conversational format
- `hindi_audiobook` - Storytelling

---

## Key Features

✅ **Single MCP Instance** - No duplicates, consistent state  
✅ **Clean Imports** - Import from package level  
✅ **Type Safety** - Pydantic models with validation  
✅ **FastMCP 2.x** - Context, ToolAnnotations, tags, progress reporting  
✅ **Production Ready** - Comprehensive error handling  
✅ **Hindi Support** - 4 Hindi voices (hf_alpha, hf_beta, hm_omega, hm_psi)  
✅ **Educational Scripts** - Dedicated tool for markdown scripts with segments
✅ **Client Logging** - Progress and status visible in MCP clients

## Documentation

- [MCP_SERVER_USAGE.md](./MCP_SERVER_USAGE.md) - Detailed usage guide
- [FastMCP Docs](https://gofastmcp.com/) - FastMCP 2.x documentation
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
**Framework**: FastMCP v2.14+  
**Protocol**: Model Context Protocol (MCP)  
**Transport**: stdio
