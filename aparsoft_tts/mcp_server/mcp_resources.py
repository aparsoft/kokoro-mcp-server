"""
Comprehensive MCP tools for Aparsoft TTS using FastMCP.

This MCP tools exposes Aparsoft TTS functionality to AI assistants like Claude Desktop,
Cursor, and other MCP-compatible clients.

🔧 MCP TOOLS IMPLEMENTED:

1. TOOLS (6 available):
   - generate_speech: Convert text to speech with voice and enhancement options
   - list_voices: Get available voices organized by gender and accent
   - batch_generate: Process multiple texts efficiently
   - process_script: Convert complete video scripts to voiceovers
   - generate_podcast: Create multi-voice conversational podcasts
   - transcribe_speech: Convert audio to text using OpenAI Whisper
"""

import warnings
import os
import platform
from pathlib import Path

from fastmcp import FastMCP

import mcp_utils

# Suppress all warnings to prevent non-JSON output in MCP
warnings.filterwarnings("ignore")

from aparsoft_tts.config import get_config
from aparsoft_tts.core.engine import TTSEngine
from aparsoft_tts.utils.logging import bind_context, get_logger, setup_logging

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

# Initialize TTS engine
try:
    tts_engine = TTSEngine()
    log.info("mcp_server_initialized", server_name=config.mcp.server_name)
except Exception as e:
    log.error("mcp_server_initialization_failed", error=str(e))
    raise

# ==============================================================================
# MCP RESOURCES - Read-only data sources for voice info, presets, etc.
# ==============================================================================
# Resources provide contextual information without execution, helping Claude
# make informed decisions about voice selection, settings, and best practices.
# Based on Kokoro-82M voice characteristics from HuggingFace documentation.


@mcp.resource("tts://voice/info/{voice_id}")
async def get_voice_info(voice_id: str) -> str:
    """Get detailed information about a specific Kokoro voice.

    Provides comprehensive voice characteristics including quality grade,
    training hours, best use cases, characteristics, and speed recommendations.

    Based on official Kokoro-82M documentation with quality grades (A-F scale)
    and training duration data (HH = 10-100 hours, H = 1-10 hours, etc.).

    Args:
        voice_id: Voice identifier (e.g., 'am_michael', 'af_bella')

    Returns:
        JSON string with voice details and recommendations

    Example URIs:
        tts://voice/info/af_bella - Premium female voice (A- grade)
        tts://voice/info/am_michael - Professional male voice (C+ grade)
        tts://voice/info/bm_george - Distinguished British male (C grade)
    """
    try:
        bind_context(operation="get_voice_info", voice_id=voice_id)

        info = mcp_utils.get_voice_info_resource(voice_id)

        log.info("mcp_resource_voice_info_retrieved", voice_id=voice_id)

        # Return formatted JSON for easy parsing
        import json

        return json.dumps(info, indent=2)

    except Exception as e:
        log.error("mcp_resource_voice_info_error", voice_id=voice_id, error=str(e))
        return json.dumps({"error": str(e), "voice_id": voice_id})


@mcp.resource("tts://voices/comparison")
async def get_voices_comparison() -> str:
    """Get comprehensive comparison of all available voices.

    Organizes voices by:
    - Quality tiers (premium, professional, casual)
    - Gender (male, female)
    - Accent (American, British)

    Helps quickly identify the best voice for specific content needs.
    Premium voices (A-B grade with HH training) recommended for long-form content.

    Returns:
        JSON string with categorized voice comparison

    Example URI:
        tts://voices/comparison - Complete voice quality comparison
    """
    try:
        bind_context(operation="get_voices_comparison")

        comparison = mcp_utils.get_all_voices_comparison()

        log.info(
            "mcp_resource_voices_comparison_retrieved",
            total_voices=comparison.get("total_voices", 0),
        )

        import json

        return json.dumps(comparison, indent=2)

    except Exception as e:
        log.error("mcp_resource_voices_comparison_error", error=str(e))
        return json.dumps({"error": str(e)})


@mcp.resource("tts://presets/{preset_name}")
async def get_preset(preset_name: str) -> str:
    """Get configuration preset for a specific use case.

    Provides pre-configured settings optimized for:
    - youtube_tutorial: Educational content with clear delivery
    - podcast_host: Warm, engaging conversational podcasts
    - audiobook_narration: Long-form storytelling
    - meditation_guide: Calm, soothing guidance
    - news_announcement: Professional news-style delivery
    - casual_vlog: Personal, casual YouTube vlogs
    - product_demo: Professional product showcases
    - documentary_narration: Authoritative documentary voiceover

    Args:
        preset_name: Preset identifier

    Returns:
        JSON string with preset configuration and tips

    Example URIs:
        tts://presets/youtube_tutorial - Tutorial preset with am_michael
        tts://presets/podcast_host - Podcast preset with af_bella
        tts://presets/audiobook_narration - Audiobook with af_bella
    """
    try:
        bind_context(operation="get_preset", preset_name=preset_name)

        preset = mcp_utils.get_preset_resource(preset_name)

        log.info("mcp_resource_preset_retrieved", preset_name=preset_name)

        import json

        return json.dumps(preset, indent=2)

    except Exception as e:
        log.error("mcp_resource_preset_error", preset_name=preset_name, error=str(e))
        return json.dumps({"error": str(e), "preset_name": preset_name})


@mcp.resource("tts://presets/all")
async def get_all_presets() -> str:
    """Get all available configuration presets organized by category.

    Categories:
    - education: Tutorial, audiobook
    - entertainment: Podcast, vlog, documentary
    - professional: News, product demo
    - wellness: Meditation guide

    Returns:
        JSON string with all presets and categorization

    Example URI:
        tts://presets/all - All available presets with recommendations
    """
    try:
        bind_context(operation="get_all_presets")

        presets = mcp_utils.get_all_presets()

        log.info("mcp_resource_all_presets_retrieved")

        import json

        return json.dumps(presets, indent=2)

    except Exception as e:
        log.error("mcp_resource_all_presets_error", error=str(e))
        return json.dumps({"error": str(e)})
