# aparsoft_tts/mcp_server/__init__.py

"""Aparsoft TTS MCP Server Package.

Model Context Protocol (MCP) server implementation using FastMCP framework.
Exposes Aparsoft TTS functionality to MCP clients (Claude Desktop, Cursor, etc.).

Package Structure:
  - mcp_server_main.py: Core server setup, Pydantic models, server initialization
  - mcp_tools.py: 6 tool implementations (@mcp.tool)
  - mcp_resources.py: 4 resource implementations (@mcp.resource)
  - mcp_prompts.py: 4 prompt implementations (@mcp.prompt)
  - mcp_utils.py: Shared utilities, voice data, preset templates

Setup:
  Add to Claude Desktop config (~/.config/Claude/claude_desktop_config.json):
  {
    "mcpServers": {
      "aparsoft-tts": {
        "command": "/path/to/venv/bin/python",
        "args": ["-m", "aparsoft_tts.mcp_server"]
      }
    }
  }

Run server: python -m aparsoft_tts.mcp_server
"""

# Import main entry point and core components from mcp_server_main
from aparsoft_tts.mcp_server.mcp_server_main import (
    main,
    mcp,
    config,
    get_tts_engine,  # Lazy loader function
    # Pydantic models for type hints/validation
    GenerateSpeechRequest,
    BatchGenerateRequest,
    ProcessScriptRequest,
    GeneratePodcastRequest,
    PodcastSegment,
    TranscribeAudioRequest,
)

# Define public API
__all__ = [
    "main",
    "mcp",
    "config",
    "get_tts_engine",  # Export getter, not the engine itself
    "GenerateSpeechRequest",
    "BatchGenerateRequest",
    "ProcessScriptRequest",
    "GeneratePodcastRequest",
    "PodcastSegment",
    "TranscribeAudioRequest",
]

# Make this module executable
if __name__ == "__main__":
    main()
