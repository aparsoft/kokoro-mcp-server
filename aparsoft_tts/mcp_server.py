"""Comprehensive MCP server for Aparsoft TTS using FastMCP.

This MCP server exposes Aparsoft TTS functionality to AI assistants like Claude Desktop,
Cursor, and other MCP-compatible clients. It provides six main tools:

1. generate_speech: Convert text to speech with voice and enhancement options
2. list_voices: Get available voices organized by gender and accent
3. batch_generate: Process multiple texts efficiently
4. process_script: Convert complete video scripts to voiceovers
5. generate_podcast: Create multi-voice conversational podcasts (see PODCAST_GUIDELINES.md)
6. transcribe_speech: Convert audio to text using OpenAI Whisper

🎙️ PODCAST GUIDELINES:
For best practices on creating natural, ethical AI podcasts, see PODCAST_GUIDELINES.md
Key requirements:
- ALWAYS include AI disclosure in first segment (Apple/YouTube requirement)
- Use conversational style with questions/reactions, NOT newsreader style
- Vary speech speeds (1.0-1.2x) based on emotional context
- Keep segments short (15-25 per episode) for dynamic feel

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
from pydantic import BaseModel, Field, field_validator

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


@mcp.tool()
async def generate_podcast(request: GeneratePodcastRequest) -> str:
    """Generate multi-voice podcast with different voices and speeds per segment.

    This tool enables podcast-style content creation with:
    - Multiple segments, each with its own voice and speed
    - Support for host/guest conversations with different voices
    - Configurable gaps between segments
    - Professional audio enhancement
    - Automatic segment combination into a single file

    Perfect for:
    - Podcast episodes with multiple speakers
    - Interview-style content with host and guest voices
    - Educational content with narrator and character voices
    - Radio-style shows with different segments

    🎙️ PODCAST BEST PRACTICES (See PODCAST_GUIDELINES.md for full details):

    ⚠️ MANDATORY AI DISCLOSURE:
    - ALWAYS include AI disclosure in the FIRST segment
    - Required by Apple Podcasts, YouTube, and ethical guidelines
    - Example: "This podcast is created using Claude by Anthropic for content
      creation and Aparsoft TTS for voice synthesis."

    ✅ NATURAL CONVERSATION (Not Newsreader Style):
    - Use questions between hosts: "What do you think about this?"
    - Add reactions: "Really?" "That's huge!" "Exactly!"
    - Vary speeds: 1.0x for important info, 1.1-1.2x for excitement
    - Keep segments short (15-25 per episode for dynamic feel)
    - Mix statement lengths: short reactions + medium explanations

    🎚️ SPEED GUIDELINES:
    - Disclosure/Important: 1.0x
    - Casual conversation: 1.0-1.05x
    - Excitement/reveals: 1.1-1.2x
    - Questions: 0.95-1.0x

    Args:
        request: Podcast generation parameters including segments list

    Returns:
        Detailed summary of generated podcast with segment breakdown

    Example - Natural Podcast Style:
        >>> await generate_podcast(GeneratePodcastRequest(
        ...     segments=[
        ...         PodcastSegment(
        ...             text="Welcome to AI Insights. Before we dive in, this podcast is "
        ...                  "created using Claude and Aparsoft TTS.",
        ...             voice="af_sarah", speed=1.0, name="disclosure_intro"
        ...         ),
        ...         PodcastSegment(
        ...             text="Thanks Sarah! Have you seen today's big announcement?",
        ...             voice="am_michael", speed=1.1, name="michael_excited"
        ...         ),
        ...         PodcastSegment(
        ...             text="I have! Are you ready for this?",
        ...             voice="af_sarah", speed=1.05, name="sarah_tease"
        ...         ),
        ...         PodcastSegment(
        ...             text="Hit me.",
        ...             voice="am_michael", speed=1.0, name="michael_ready"
        ...         )
        ...     ],
        ...     output_path="podcast_episode.wav",
        ...     gap_duration=0.4
        ... ))
    """
    try:
        # Bind context for logging
        bind_context(
            operation="generate_podcast",
            num_segments=len(request.segments),
            voices_used=list(set(seg.voice for seg in request.segments)),
        )

        # Use config default if gap_duration not specified
        gap_duration = (
            request.gap_duration
            if request.gap_duration is not None
            else config.tts.podcast_default_gap
        )

        log.info(
            "mcp_generate_podcast_request",
            num_segments=len(request.segments),
            gap_duration=gap_duration,
            enhance=request.enhance,
        )

        # Validate segments
        if not request.segments:
            raise ValueError("At least one segment is required")

        # Normalize output path
        output_path_input = normalize_path(request.output_path)
        if not output_path_input.is_absolute():
            output_path_input = Path.cwd() / output_path_input

        # Ensure output directory exists
        output_path_input.parent.mkdir(parents=True, exist_ok=True)
        output_path_abs = str(output_path_input.resolve())

        log.info("mcp_generate_podcast_starting", output_path=output_path_abs)

        # Generate each segment
        audio_segments = []
        segment_details = []

        for i, segment in enumerate(request.segments, 1):
            segment_name = segment.name or f"segment_{i}"

            log.info(
                "mcp_generate_podcast_segment",
                segment_num=i,
                segment_name=segment_name,
                voice=segment.voice,
                speed=segment.speed,
                text_length=len(segment.text),
            )

            try:
                # Generate audio for this segment
                audio = tts_engine.generate(
                    text=segment.text,
                    voice=segment.voice,
                    speed=segment.speed,
                    enhance=request.enhance,
                )

                # Ensure we have numpy array, not Path
                if isinstance(audio, Path):
                    raise AparsoftTTSError(
                        f"Unexpected Path return for segment {i}. Expected audio array."
                    )

                audio_segments.append(audio)

                # Track segment details for summary
                from aparsoft_tts.utils.audio import get_audio_duration

                duration = get_audio_duration(audio, config.tts.sample_rate)
                segment_details.append(
                    {
                        "name": segment_name,
                        "voice": segment.voice,
                        "speed": segment.speed,
                        "duration": duration,
                        "text_preview": segment.text[:50]
                        + ("..." if len(segment.text) > 50 else ""),
                    }
                )

                log.info(
                    "mcp_generate_podcast_segment_complete",
                    segment_num=i,
                    duration=duration,
                )

            except Exception as e:
                log.error(
                    "mcp_generate_podcast_segment_failed",
                    segment_num=i,
                    segment_name=segment_name,
                    error=str(e),
                )
                raise AparsoftTTSError(
                    f"Failed to generate segment {i} ({segment_name}): {str(e)}"
                ) from e

        # Combine segments with gaps
        log.info("mcp_generate_podcast_combining", num_segments=len(audio_segments))

        from aparsoft_tts.utils.audio import combine_audio_segments, save_audio

        combined_audio = combine_audio_segments(
            audio_segments,
            sample_rate=config.tts.sample_rate,
            gap_duration=gap_duration,
            crossfade_duration=config.tts.podcast_crossfade_duration,
        )

        # Save combined audio
        output_path = save_audio(
            combined_audio,
            output_path_abs,
            sample_rate=config.tts.sample_rate,
            format=config.tts.output_format,
        )

        # Get final file stats
        actual_path = Path(output_path).resolve()
        file_size = actual_path.stat().st_size
        total_duration = get_audio_duration(combined_audio, config.tts.sample_rate)

        # Build detailed summary
        result = f"""✅ Podcast generated successfully!

📁 FULL PATH: {actual_path}

📊 PODCAST DETAILS:
Total Segments: {len(request.segments)}
Total Duration: {total_duration:.1f}s ({total_duration / 60:.1f} min)
File Size: {file_size / 1024 / 1024:.2f} MB
Gap Duration: {gap_duration}s
Audio Enhanced: {request.enhance}

🎙️ SEGMENT BREAKDOWN:
"""

        for i, detail in enumerate(segment_details, 1):
            result += f"""  {i}. {detail['name']}
     Voice: {detail['voice']}
     Speed: {detail['speed']}x
     Duration: {detail['duration']:.1f}s
     Text: "{detail['text_preview']}"

"""

        result += f"""Your podcast is ready to publish!"""

        log.info(
            "mcp_generate_podcast_success",
            output_path=str(actual_path),
            num_segments=len(request.segments),
            total_duration=total_duration,
            file_size_mb=file_size / 1024 / 1024,
        )

        return result

    except ValueError as e:
        log.error("mcp_generate_podcast_validation_error", error=str(e))
        return f"❌ Validation Error: {str(e)}"
    except AparsoftTTSError as e:
        log.error("mcp_generate_podcast_error", error=str(e))
        return f"❌ Error: {str(e)}"
    except Exception as e:
        log.error("mcp_generate_podcast_unexpected_error", error=str(e))
        return f"❌ Unexpected error: {str(e)}"


@mcp.tool()
async def transcribe_speech(request: TranscribeAudioRequest) -> str:
    """Transcribe audio file to text using OpenAI Whisper.

    Convert speech in audio files (WAV, MP3, MP4, etc.) to written text.
    Perfect for transcribing voiceovers, interviews, meetings, or any audio content.

    Features:
    - Multiple model sizes (tiny to large) for speed/accuracy tradeoff
    - Automatic language detection
    - Translation to English
    - Support for 99 languages
    - Handles background noise and various accents

    Note: Requires 'openai-whisper' package. Install with:
    pip install openai-whisper

    Args:
        request: Transcription parameters

    Returns:
        Success message with transcription details and file location

    Example:
        >>> await transcribe_speech(TranscribeAudioRequest(
        ...     audio_path="interview.wav",
        ...     output_path="interview_transcript.txt",
        ...     model_size="base"
        ... ))
    """
    try:
        # Bind request context for logging
        bind_context(
            operation="transcribe_speech",
            model_size=request.model_size,
        )

        # Normalize audio path
        audio_path_input = normalize_path(request.audio_path)
        if not audio_path_input.is_absolute():
            audio_path_input = Path.cwd() / audio_path_input

        # Check if file exists
        if not audio_path_input.exists():
            return f"❌ Error: Audio file not found: {audio_path_input}"

        audio_path_abs = str(audio_path_input.resolve())

        # Normalize output path
        output_path_input = normalize_path(request.output_path)
        if not output_path_input.is_absolute():
            output_path_input = Path.cwd() / output_path_input

        # Ensure output directory exists
        output_path_input.parent.mkdir(parents=True, exist_ok=True)
        output_path_abs = str(output_path_input.resolve())

        log.info(
            "mcp_transcribe_speech_request",
            audio_path=audio_path_abs,
            output_path=output_path_abs,
            model_size=request.model_size,
        )

        # Import transcription function
        from aparsoft_tts.utils.audio import transcribe_audio

        # Transcribe audio
        language = request.language if request.language else None
        result = transcribe_audio(
            audio_path=audio_path_abs,
            output_path=output_path_abs,
            model_size=request.model_size,
            language=language,
            task=request.task,
        )

        # Get file stats
        actual_path = Path(output_path_abs).resolve()
        file_size = actual_path.stat().st_size
        transcription_text = result["text"]
        detected_language = result["language"]
        num_segments = len(result.get("segments", []))

        # Create preview (first 200 characters)
        preview = (
            transcription_text[:200] + "..."
            if len(transcription_text) > 200
            else transcription_text
        )

        result_msg = f"""✅ Audio transcribed successfully!

📁 FULL PATH: {actual_path}

📊 TRANSCRIPTION DETAILS:
Audio File: {Path(audio_path_abs).name}
Output File: {actual_path.name}
Model Used: {request.model_size}
Detected Language: {detected_language}
Task: {request.task}
Text Length: {len(transcription_text)} characters
Word Count: ~{len(transcription_text.split())} words
Segments: {num_segments}
File Size: {file_size / 1024:.1f} KB

📝 PREVIEW:
"{preview}"

Your transcription is ready!"""

        log.info(
            "mcp_transcribe_speech_success",
            output_path=str(actual_path),
            text_length=len(transcription_text),
            language=detected_language,
        )

        return result_msg

    except ImportError as e:
        log.error("mcp_transcribe_speech_import_error", error=str(e))
        return """❌ Error: OpenAI Whisper is not installed.

To use speech-to-text functionality, install it with:

pip install openai-whisper

Also ensure ffmpeg is installed on your system:
- Ubuntu/Debian: sudo apt-get install ffmpeg
- macOS: brew install ffmpeg
- Windows: Download from https://ffmpeg.org/download.html"""
    except FileNotFoundError as e:
        log.error("mcp_transcribe_speech_file_not_found", error=str(e))
        return f"❌ Audio file not found: {request.audio_path}\n\nPlease check the file path and try again."
    except AparsoftTTSError as e:
        log.error("mcp_transcribe_speech_error", error=str(e), error_type=type(e).__name__)
        return f"❌ Error: {str(e)}"
    except Exception as e:
        log.error("mcp_transcribe_speech_unexpected_error", error=str(e))
        return f"❌ Unexpected error: {str(e)}\n\nPlease check your audio file and system setup."


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
