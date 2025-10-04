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
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from aparsoft_tts.config import get_config
from aparsoft_tts.core.engine import ALL_VOICES, FEMALE_VOICES, MALE_VOICES, TTSEngine
from aparsoft_tts.utils.exceptions import AparsoftTTSError
from aparsoft_tts.utils.logging import bind_context, get_logger, setup_logging

# Initialize logging
setup_logging()
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
        description="Output filename",
    )
    enhance: bool = Field(
        default=True,
        description="Apply audio enhancement (normalization, noise reduction, etc.)",
    )


class BatchGenerateRequest(BaseModel):
    """Request model for batch_generate tool."""

    texts: list[str] = Field(..., description="List of texts to convert", min_length=1)
    output_dir: str = Field(default="outputs", description="Output directory")
    voice: str = Field(default="am_michael", description="Voice to use")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class ProcessScriptRequest(BaseModel):
    """Request model for process_script tool."""

    script_path: str = Field(..., description="Path to script file")
    output_path: str = Field(default="voiceover.wav", description="Output file path")
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

        log.info(
            "mcp_generate_speech_request",
            voice=request.voice,
            speed=request.speed,
            enhance=request.enhance,
            output_file=request.output_file,
        )

        # Generate speech
        output_path = tts_engine.generate(
            text=request.text,
            output_path=request.output_file,
            voice=request.voice,
            speed=request.speed,
            enhance=request.enhance,
        )

        # Get file size
        file_size = Path(output_path).stat().st_size
        duration = len(request.text) * 0.08  # Rough estimate

        log.info(
            "mcp_generate_speech_success",
            output_file=str(output_path),
            size_bytes=file_size,
        )

        return f"""✅ Speech generated successfully!

File: {output_path}
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

        log.info(
            "mcp_batch_generate_request",
            num_texts=len(request.texts),
            output_dir=request.output_dir,
        )

        paths = tts_engine.batch_generate(
            texts=request.texts,
            output_dir=request.output_dir,
            voice=request.voice,
            speed=request.speed,
        )

        result = f"""✅ Batch generation completed!

Generated {len(paths)} audio files:
"""
        for i, path in enumerate(paths, 1):
            size = Path(path).stat().st_size
            result += f"  {i}. {path.name} ({size / 1024:.1f} KB)\n"

        result += f"\nOutput directory: {request.output_dir}\n"
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

        log.info(
            "mcp_process_script_request",
            script_path=request.script_path,
            output_path=request.output_path,
        )

        output_path = tts_engine.process_script(
            script_path=request.script_path,
            output_path=request.output_path,
            gap_duration=request.gap_duration,
            voice=request.voice,
            speed=request.speed,
        )

        file_size = Path(output_path).stat().st_size

        result = f"""✅ Script processed successfully!

Output: {output_path}
Size: {file_size / 1024 / 1024:.2f} MB
Voice: {request.voice}
Speed: {request.speed}x
Gap between segments: {request.gap_duration}s

Your complete voiceover is ready to use!"""

        log.info("mcp_process_script_success", output_path=str(output_path))
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
