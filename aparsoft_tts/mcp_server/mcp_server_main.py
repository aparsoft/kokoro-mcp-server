# aparsoft_tts/mcp_server/mcp_server_main.py

"""Main entry point for Aparsoft TTS MCP Server using FastMCP.

This module provides the core server setup, Pydantic request models, and main()
entry point. The actual MCP components are implemented in separate modules:
- mcp_tools.py: Tool implementations (@mcp.tool decorators)
- mcp_resources.py: Resource implementations (@mcp.resource decorators)
- mcp_prompts.py: Prompt implementations (@mcp.prompt decorators)
- mcp_utils.py: Shared utility functions

The server exposes Aparsoft TTS functionality to MCP clients (Claude Desktop, Cursor, etc.)
using FastMCP's stdio transport for standardized Model Context Protocol communication.

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

Components:
  - 6 Tools: generate_speech, list_voices, batch_generate, process_script,
             generate_podcast, transcribe_speech
  - 4 Resources: voice info, voice comparison, presets
  - 4 Prompts: podcast_creator, voice_selector, script_optimizer, troubleshoot_tts

See individual module files for detailed component documentation.
"""

import asyncio
import warnings
import os
import platform
from pathlib import Path, PureWindowsPath, PurePosixPath
from typing import Any

from fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator

# Suppress all warnings to prevent non-JSON output in MCP
warnings.filterwarnings("ignore")

from aparsoft_tts.config import get_config
from aparsoft_tts.core.engine import ALL_VOICES, TTSEngine
from aparsoft_tts.utils.logging import get_logger, setup_logging

# Initialize logging - force stderr for MCP compatibility
import os
import logging
from aparsoft_tts.config import LoggingConfig

# Suppress ALL non-structlog logging to prevent JSON parsing errors in MCP
# This prevents library warnings and other non-JSON output from interfering
logging.root.handlers.clear()
logging.root.addHandler(logging.NullHandler())
logging.root.setLevel(logging.CRITICAL + 1)

# Suppress specific noisy loggers that might output to stderr
for logger_name in [
    "PIL",
    "matplotlib",
    "kokoro",
    "transformers",
    "torch",
    "librosa",
    "soundfile",
    "numba",
    "urllib3",
    "huggingface_hub",
]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL + 1)
    logging.getLogger(logger_name).propagate = False
    logging.getLogger(logger_name).addHandler(logging.NullHandler())

# Create MCP-compatible logging config
mcp_logging_config = LoggingConfig(
    level=os.getenv("LOG_LEVEL", "ERROR"),  # Only errors by default
    format="json",
    output="stderr",  # Always use stderr for MCP
    include_timestamp=False,  # Reduce noise
    include_caller=False,
)
setup_logging(mcp_logging_config)
log = get_logger(__name__)

# Get configuration
config = get_config()

# Initialize FastMCP server
mcp = FastMCP(config.mcp.server_name, version=config.mcp.server_version)

# TTS engine - LAZY INITIALIZATION
# Don't load the model at import time! Load only when first needed.
# This prevents blocking Claude Desktop/Cursor during MCP server startup.
tts_engine: TTSEngine | None = None


def get_tts_engine() -> TTSEngine:
    """Get or initialize the TTS engine (lazy loading).

    The engine is only initialized on first use, not at module import.
    This ensures fast MCP server startup for Claude Desktop/Cursor.
    """
    global tts_engine
    if tts_engine is None:
        log.info("initializing_tts_engine", msg="First use - loading model...")
        tts_engine = TTSEngine()
        log.info("tts_engine_ready", msg="Model loaded successfully")
    return tts_engine


# Pydantic models for request validation
class GenerateSpeechRequest(BaseModel):
    """Request model for generate_speech tool."""

    text: str = Field(..., description="Text to convert to speech", min_length=1, max_length=10000)
    voice: str = Field(
        default="am_michael",
        description=f"Voice ID. Available: {', '.join(ALL_VOICES)}",
    )
    speed: float = Field(
        default=1.0,
        description="Speech speed (0.5-2.0)",
        ge=0.5,
        le=2.0,
    )
    output_file: str = Field(
        default="output.wav",
        description="Output file path (absolute or relative to current directory)",
    )
    enhance: bool = Field(
        default=True,
        description="Apply audio enhancement (normalization, noise reduction, etc.)",
    )


class BatchGenerateRequest(BaseModel):
    """Request model for batch_generate tool."""

    texts: list[str] = Field(..., description="List of texts to convert", min_length=1)
    output_dir: str = Field(
        default="outputs",
        description="Output directory (absolute or relative to current directory)",
    )
    voice: str = Field(default="am_michael", description="Voice to use")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class ProcessScriptRequest(BaseModel):
    """Request model for process_script tool."""

    script_path: str = Field(
        ..., description="Path to script file (absolute or relative to current directory)"
    )
    output_path: str = Field(
        default="voiceover.wav",
        description="Output file path (absolute or relative to current directory)",
    )
    gap_duration: float = Field(
        default=0.5, description="Gap between segments in seconds", ge=0.0, le=5.0
    )
    voice: str = Field(default="am_michael", description="Voice to use")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class PodcastSegment(BaseModel):
    """Model for a single podcast segment with voice and speed control."""

    text: str = Field(..., description="Segment text content", min_length=1, max_length=10000)
    voice: str = Field(
        default="am_michael",
        description=f"Voice for this segment. Available: {', '.join(ALL_VOICES)}",
    )
    speed: float = Field(
        default=1.0, description="Speech speed for this segment (0.5-2.0)", ge=0.5, le=2.0
    )
    name: str = Field(default="", description="Optional segment name/label for identification")

    @field_validator("voice")
    @classmethod
    def validate_voice(cls, v: str) -> str:
        """Validate voice is in available voices."""
        if v not in ALL_VOICES:
            raise ValueError(f"Invalid voice '{v}'. Must be one of: {', '.join(ALL_VOICES)}")
        return v


class TranscribeAudioRequest(BaseModel):
    """Request model for transcribe_speech tool."""

    audio_path: str = Field(
        ..., description="Path to audio file (wav, mp3, mp4, etc.) - absolute or relative"
    )
    output_path: str = Field(
        default="transcript.txt",
        description="Output text file path (absolute or relative to current directory)",
    )
    model_size: str = Field(
        default="base",
        description="Whisper model size: tiny, base, small, medium, large (larger = more accurate)",
    )
    language: str = Field(
        default="",
        description="Language code (e.g., 'en', 'es', 'fr'). Leave empty for auto-detection",
    )
    task: str = Field(
        default="transcribe",
        description="Task: 'transcribe' (same language) or 'translate' (to English)",
    )

    @field_validator("model_size")
    @classmethod
    def validate_model_size(cls, v: str) -> str:
        """Validate model size."""
        valid_sizes = ["tiny", "base", "small", "medium", "large"]
        if v not in valid_sizes:
            raise ValueError(f"Invalid model size '{v}'. Must be one of: {', '.join(valid_sizes)}")
        return v

    @field_validator("task")
    @classmethod
    def validate_task(cls, v: str) -> str:
        """Validate task type."""
        valid_tasks = ["transcribe", "translate"]
        if v not in valid_tasks:
            raise ValueError(f"Invalid task '{v}'. Must be one of: {', '.join(valid_tasks)}")
        return v


class GeneratePodcastRequest(BaseModel):
    """Request model for generate_podcast tool."""

    segments: list[PodcastSegment] = Field(
        ...,
        description="List of podcast segments with individual voice/speed settings",
        min_length=1,
    )
    output_path: str = Field(
        default="podcast.wav",
        description="Output file path (absolute or relative to current directory)",
    )
    gap_duration: float = Field(
        default=None,  # Will use config default if not provided
        description="Gap between segments in seconds (uses config default if not specified)",
        ge=0.0,
        le=5.0,
    )
    enhance: bool = Field(default=True, description="Apply audio enhancement to all segments")

    @field_validator("segments")
    @classmethod
    def validate_segments_count(cls, v: list[PodcastSegment]) -> list[PodcastSegment]:
        """Validate segments count doesn't exceed maximum."""
        max_segments = config.tts.podcast_max_segments
        if len(v) > max_segments:
            raise ValueError(f"Too many segments: {len(v)}. Maximum allowed: {max_segments}")
        return v


def main() -> None:
    """Run the MCP server.

    This starts the FastMCP server using stdio transport, making it compatible
    with Claude Desktop, Cursor, and other MCP clients.
    """
    log.info("starting_mcp_server", transport=config.mcp.transport)

    try:
        # Run the server with banner display
        mcp.run(transport="stdio", show_banner=True)
    except KeyboardInterrupt:
        log.info("mcp_server_stopped_by_user")
    except Exception as e:
        log.error("mcp_server_error", error=str(e))
        raise


if __name__ == "__main__":
    main()
