"""Comprehensive MCP server for Aparsoft TTS using FastMCP.

This MCP server exposes Aparsoft TTS functionality to AI assistants like Claude Desktop,
Cursor, and other MCP-compatible clients. It provides four main tools:

1. generate_speech: Convert text to speech with voice and enhancement options
2. list_voices: Get available voices organized by gender and accent
3. batch_generate: Process multiple texts efficiently
4. process_script: Convert complete video scripts to voiceovers

The server uses FastMCP (https://github.com/jlowin/fastmcp) for standardized
MCP protocol implementation with features like:
- Automatic tool schema generation from Python type hints
- Request validation with Pydantic models
- Structured logging with correlation IDs
- Comprehensive error handling
- stdio transport for local MCP clients

Setup Instructions:

1. For Claude Desktop (~/.config/Claude/claude_desktop_config.json or
   ~/Library/Application Support/Claude/claude_desktop_config.json on macOS):

   {
     "mcpServers": {
       "aparsoft-tts": {
         "command": "/absolute/path/to/venv/bin/python",
         "args": ["-m", "aparsoft_tts.mcp_server"]
       }
     }
   }

2. For Cursor (~/.cursor/mcp.json):

   {
     "mcpServers": {
       "aparsoft-tts": {
         "command": "/absolute/path/to/venv/bin/python",
         "args": ["-m", "aparsoft_tts.mcp_server"]
       }
     }
   }

3. Restart your MCP client to load the server

Usage Examples:
- "Generate speech for 'Welcome to my channel' using am_michael voice"
- "List all available TTS voices"
- "Process my script.txt file and create a voiceover"
- "Batch generate audio for these three segments"

Debugging:
- Check logs in the client's log directory
- Use MCP Inspector for interactive testing: npx @modelcontextprotocol/inspector
- Enable debug logging with LOG_LEVEL=DEBUG environment variable
"""

import asyncio
import warnings
import os
import platform
from pathlib import Path, PureWindowsPath, PurePosixPath
from typing import Any

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Suppress all warnings to prevent non-JSON output in MCP
warnings.filterwarnings("ignore")

from aparsoft_tts.config import get_config
from aparsoft_tts.core.engine import ALL_VOICES, FEMALE_VOICES, MALE_VOICES, TTSEngine
from aparsoft_tts.utils.exceptions import AparsoftTTSError
from aparsoft_tts.utils.logging import bind_context, get_logger, setup_logging

# Initialize logging - force stderr for MCP compatibility
import sys
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

# Initialize TTS engine
try:
    tts_engine = TTSEngine()
    log.info("mcp_server_initialized", server_name=config.mcp.server_name)
except Exception as e:
    log.error("mcp_server_initialization_failed", error=str(e))
    raise


def normalize_path(path_str: str) -> Path:
    """Normalize paths to handle Windows, Linux, and WSL paths robustly.

    This function handles three types of paths:
    1. WSL paths: \\wsl.localhost\\Ubuntu\\home\\user\\file.txt
    2. Windows paths: C:\\Users\\user\\file.txt
    3. Linux paths: /home/user/file.txt

    Args:
        path_str: Input path string

    Returns:
        Normalized Path object that works on the current platform

    Example:
        normalize_path("\\\\wsl.localhost\\\\Ubuntu\\\\home\\\\ram\\\\test.wav")
    """
    path_str = path_str.strip()

    # Detect WSL path by looking for 'wsl.localhost' or 'wsl\localhost' patterns
    # This handles various formats that Windows/Claude might send
    is_wsl_path = (
        "wsl.localhost" in path_str.lower()
        or "wsl\\localhost" in path_str.lower()
        or "wsl/localhost" in path_str.lower()
    )

    if is_wsl_path:
        # Extract the Linux path portion
        # Format: \\wsl.localhost\\Ubuntu\\home\\user\\file.txt -> /home/user/file.txt
        parts = path_str.replace("\\", "/").split("/")
        # Remove empty strings and 'wsl.localhost' and distro name
        parts = [p for p in parts if p and p not in ("wsl.localhost", "wsl", "localhost")]
        if parts and parts[0].lower() in ("ubuntu", "debian", "kali", "alpine", "arch", "fedora"):
            parts.pop(0)  # Remove distro name

        linux_path = "/" + "/".join(parts)

        # If we're on WSL/Linux, use the extracted Linux path directly
        if platform.system() == "Linux" or os.path.exists("/proc/version"):
            return Path(linux_path)
        else:
            # On Windows, keep the WSL path format
            return Path(path_str)

    # For Windows absolute paths (C:\\, D:\\, etc.) or Linux absolute paths (/home, /usr, etc.)
    # Just use Path directly - it will handle them correctly
    return Path(path_str)


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


@mcp.tool()
async def generate_speech(request: GenerateSpeechRequest) -> str:
    """Generate high-quality speech from text using Kokoro TTS.

    This tool converts text to natural-sounding speech with professional
    audio enhancement. Perfect for creating YouTube voiceovers, podcasts,
    and other audio content.

    Features:
    - Multiple voice options (male/female, American/British)
    - Adjustable speech speed
    - Automatic audio enhancement (noise reduction, normalization)
    - Production-quality output

    Args:
        request: Speech generation parameters

    Returns:
        Success message with file details

    Example:
        >>> await generate_speech(GenerateSpeechRequest(
        ...     text="Welcome to our channel",
        ...     voice="am_michael",
        ...     output_file="intro.wav"
        ... ))
    """
    try:
        # Bind request context for logging
        bind_context(
            operation="generate_speech",
            voice=request.voice,
            text_length=len(request.text),
        )

        # Normalize the path to handle WSL/Windows/Linux paths
        output_path_input = normalize_path(request.output_file)

        # If it's a relative path, make it absolute from cwd
        if not output_path_input.is_absolute():
            output_path_input = Path.cwd() / output_path_input

        # Ensure parent directory exists
        output_path_input.parent.mkdir(parents=True, exist_ok=True)

        # Convert to string for engine
        output_file_abs = str(output_path_input.resolve())

        log.info(
            "mcp_generate_speech_request",
            voice=request.voice,
            speed=request.speed,
            enhance=request.enhance,
            output_file=output_file_abs,
        )

        # Generate speech with absolute path
        output_path = tts_engine.generate(
            text=request.text,
            output_path=output_file_abs,
            voice=request.voice,
            speed=request.speed,
            enhance=request.enhance,
        )

        # Get file size and actual path
        actual_path = Path(output_path).resolve()
        file_size = actual_path.stat().st_size
        duration = len(request.text) * 0.08  # Rough estimate

        log.info(
            "mcp_generate_speech_success",
            output_file=str(actual_path),
            size_bytes=file_size,
        )

        return f"""✅ Speech generated successfully!

📁 FULL PATH: {actual_path}

File: {actual_path.name}
Voice: {request.voice}
Speed: {request.speed}x
Enhanced: {request.enhance}
Size: {file_size / 1024:.1f} KB
Estimated Duration: {duration:.1f}s

The audio file has been saved and is ready to use."""

    except AparsoftTTSError as e:
        log.error("mcp_generate_speech_error", error=str(e), error_type=type(e).__name__)
        return f"❌ Error: {str(e)}"
    except Exception as e:
        log.error("mcp_generate_speech_unexpected_error", error=str(e))
        return f"❌ Unexpected error: {str(e)}"


@mcp.tool()
async def list_voices() -> str:
    """List all available TTS voices.

    Returns detailed information about available voices organized by
    gender and accent.

    Returns:
        Formatted list of available voices

    Example:
        >>> await list_voices()
    """
    try:
        log.info("mcp_list_voices_request")

        voices = tts_engine.list_voices()

        result = """🎤 Available Voices

**Male Voices (Professional, Clear):**
"""
        for voice in voices["male"]:
            accent = "American" if voice.startswith("am_") else "British"
            result += f"  • {voice} - {accent} male\n"

        result += "\n**Female Voices (Warm, Expressive):**\n"
        for voice in voices["female"]:
            accent = "American" if voice.startswith("af_") else "British"
            result += f"  • {voice} - {accent} female\n"

        result += f"\n**Recommended for YouTube:** am_michael (professional, clear)\n"
        result += f"**Total Voices:** {len(MALE_VOICES) + len(FEMALE_VOICES)}\n"

        log.info("mcp_list_voices_success")
        return result

    except Exception as e:
        log.error("mcp_list_voices_error", error=str(e))
        return f"❌ Error listing voices: {str(e)}"


@mcp.tool()
async def batch_generate(request: BatchGenerateRequest) -> str:
    """Generate multiple audio files from a list of texts.

    Useful for creating multiple voiceover segments for a video project.
    Each text is saved as a separate audio file in the specified directory.

    Args:
        request: Batch generation parameters

    Returns:
        Summary of generated files

    Example:
        >>> await batch_generate(BatchGenerateRequest(
        ...     texts=["Intro", "Main content", "Outro"],
        ...     output_dir="segments/"
        ... ))
    """
    try:
        bind_context(operation="batch_generate", num_texts=len(request.texts))

        # Normalize and convert to absolute path
        output_dir_path = normalize_path(request.output_dir)
        if not output_dir_path.is_absolute():
            output_dir_path = Path.cwd() / output_dir_path

        output_dir_abs = str(output_dir_path.resolve())

        log.info(
            "mcp_batch_generate_request",
            num_texts=len(request.texts),
            output_dir=output_dir_abs,
        )

        paths = tts_engine.batch_generate(
            texts=request.texts,
            output_dir=output_dir_abs,
            voice=request.voice,
            speed=request.speed,
        )

        result = f"""✅ Batch generation completed!

Generated {len(paths)} audio files:
"""
        for i, path in enumerate(paths, 1):
            abs_path = Path(path).resolve()
            size = abs_path.stat().st_size
            result += f"  {i}. {abs_path} ({size / 1024:.1f} KB)\n"

        result += f"\n📁 OUTPUT DIRECTORY: {output_dir_path.resolve()}\n"
        result += f"Voice: {request.voice}\n"

        log.info("mcp_batch_generate_success", num_files=len(paths))
        return result

    except AparsoftTTSError as e:
        log.error("mcp_batch_generate_error", error=str(e))
        return f"❌ Error: {str(e)}"
    except Exception as e:
        log.error("mcp_batch_generate_unexpected_error", error=str(e))
        return f"❌ Unexpected error: {str(e)}"


@mcp.tool()
async def process_script(request: ProcessScriptRequest) -> str:
    """Process a complete video script file.

    Reads a text file, splits it by paragraphs, generates audio for each segment,
    and combines them with gaps into a single voiceover file. Perfect for
    creating complete YouTube video voiceovers.

    Args:
        request: Script processing parameters

    Returns:
        Summary of processed script

    Example:
        >>> await process_script(ProcessScriptRequest(
        ...     script_path="my_video_script.txt",
        ...     output_path="complete_voiceover.wav"
        ... ))
    """
    try:
        bind_context(operation="process_script", script_path=request.script_path)

        # Normalize and convert script path to absolute
        script_path_input = normalize_path(request.script_path)
        if not script_path_input.is_absolute():
            script_path_input = Path.cwd() / script_path_input
        script_path_abs = str(script_path_input.resolve())

        # Normalize and convert output path to absolute
        output_path_input = normalize_path(request.output_path)
        if not output_path_input.is_absolute():
            output_path_input = Path.cwd() / output_path_input

        # Ensure output directory exists
        output_path_input.parent.mkdir(parents=True, exist_ok=True)
        output_path_abs = str(output_path_input.resolve())

        log.info(
            "mcp_process_script_request",
            script_path=script_path_abs,
            output_path=output_path_abs,
        )

        output_path = tts_engine.process_script(
            script_path=script_path_abs,
            output_path=output_path_abs,
            gap_duration=request.gap_duration,
            voice=request.voice,
            speed=request.speed,
        )

        actual_path = Path(output_path).resolve()
        file_size = actual_path.stat().st_size

        result = f"""✅ Script processed successfully!

📁 FULL PATH: {actual_path}

Output: {actual_path.name}
Size: {file_size / 1024 / 1024:.2f} MB
Voice: {request.voice}
Speed: {request.speed}x
Gap between segments: {request.gap_duration}s

Your complete voiceover is ready to use!"""

        log.info("mcp_process_script_success", output_path=str(actual_path))
        return result

    except FileNotFoundError as e:
        log.error("mcp_process_script_file_not_found", error=str(e))
        return f"❌ Script file not found: {request.script_path}"
    except AparsoftTTSError as e:
        log.error("mcp_process_script_error", error=str(e))
        return f"❌ Error: {str(e)}"
    except Exception as e:
        log.error("mcp_process_script_unexpected_error", error=str(e))
        return f"❌ Unexpected error: {str(e)}"


def main() -> None:
    """Run the MCP server.

    This starts the FastMCP server using stdio transport, making it compatible
    with Claude Desktop, Cursor, and other MCP clients.
    """
    log.info("starting_mcp_server", transport=config.mcp.transport)

    try:
        # Run the server
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        log.info("mcp_server_stopped_by_user")
    except Exception as e:
        log.error("mcp_server_error", error=str(e))
        raise


if __name__ == "__main__":
    main()
