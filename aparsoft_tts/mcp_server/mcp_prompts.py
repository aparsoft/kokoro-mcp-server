# aparsoft_tts/mcp_server/mcp_prompts.py

"""MCP Prompts implementation for Aparsoft TTS.

Implements 4 guided workflow prompts using FastMCP's @mcp.prompt decorator:
  - podcast_creator: Step-by-step podcast creation guide with MANDATORY AI disclosure
  - voice_selector: Interactive voice selection based on content requirements
  - script_optimizer: Best practices for TTS-optimized script writing
  - troubleshoot_tts: Diagnostic guide for common quality issues

Prompts provide reusable templates and workflows to guide users through complex tasks.
Each prompt uses Pydantic models for parameter validation and generates contextual
guidance based on user requirements.

Utility functions are imported from mcp_utils.py for template generation.
"""

import warnings
from pydantic import BaseModel, Field, field_validator

from aparsoft_tts.mcp_server import mcp_utils
from aparsoft_tts.mcp_server.mcp_server_main import mcp

# Suppress all warnings to prevent non-JSON output in MCP
warnings.filterwarnings("ignore")

from aparsoft_tts.utils.logging import bind_context, get_logger

log = get_logger(__name__)


# ==============================================================================
# MCP PROMPTS - Guided workflows and best practice templates
# ==============================================================================
# Prompts guide users through complex workflows like podcast creation and
# voice selection, enforcing best practices (e.g., mandatory AI disclosure).


class PodcastPromptArgs(BaseModel):
    """Arguments for podcast creation prompt."""

    topic: str = Field(description="Podcast topic or theme")
    duration_minutes: int = Field(default=10, description="Target duration in minutes", ge=1, le=60)
    num_hosts: int = Field(default=2, description="Number of hosts/speakers", ge=1, le=4)
    style: str = Field(default="conversational", description="Podcast style")

    @field_validator("style")
    @classmethod
    def validate_style(cls, v: str) -> str:
        """Validate podcast style."""
        valid_styles = ["conversational", "interview", "educational", "news", "storytelling"]
        if v.lower() not in valid_styles:
            raise ValueError(f"Style must be one of: {', '.join(valid_styles)}")
        return v.lower()


@mcp.prompt()
async def podcast_creator(args: PodcastPromptArgs) -> str:
    """Guide for creating professional AI-generated podcasts.

    Provides comprehensive step-by-step guidance including:
    1. MANDATORY AI disclosure (legal/ethical requirement)
    2. Content structure and segmentation
    3. Voice and speed selection
    4. Natural dialogue writing tips
    5. Technical settings optimization

    ⚠️ CRITICAL: First segment MUST include AI disclosure per:
    - Apple Podcasts guidelines
    - YouTube ToS for AI content
    - Spotify recommendations

    Args:
        args: Podcast parameters (topic, duration, hosts, style)

    Returns:
        Comprehensive podcast creation guide with examples

    Example:
        >>> await podcast_creator(PodcastPromptArgs(
        ...     topic="Artificial Intelligence Ethics",
        ...     duration_minutes=15,
        ...     num_hosts=2,
        ...     style="conversational"
        ... ))
    """
    try:
        bind_context(
            operation="podcast_creator_prompt",
            topic=args.topic,
            duration=args.duration_minutes,
            style=args.style,
        )

        guide = mcp_utils.create_podcast_prompt(
            topic=args.topic,
            duration_minutes=args.duration_minutes,
            num_hosts=args.num_hosts,
            style=args.style,
        )

        log.info(
            "mcp_prompt_podcast_creator_generated",
            topic=args.topic,
            duration=args.duration_minutes,
            num_hosts=args.num_hosts,
            style=args.style,
        )

        return guide

    except Exception as e:
        log.error("mcp_prompt_podcast_creator_error", error=str(e))
        return f"❌ Error generating podcast guide: {str(e)}"


class VoiceSelectionPromptArgs(BaseModel):
    """Arguments for voice selection prompt."""

    content_type: str = Field(description="Type of content to create")
    tone: str = Field(default="professional", description="Desired tone")
    audience: str = Field(default="adults", description="Target audience")
    duration: str = Field(default="medium", description="Content duration")

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v: str) -> str:
        """Validate tone."""
        valid_tones = ["professional", "casual", "warm", "authoritative", "energetic", "calm"]
        if v.lower() not in valid_tones:
            raise ValueError(f"Tone must be one of: {', '.join(valid_tones)}")
        return v.lower()

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: str) -> str:
        """Validate duration."""
        valid_durations = ["short", "medium", "long"]
        if v.lower() not in valid_durations:
            raise ValueError(f"Duration must be one of: {', '.join(valid_durations)}")
        return v.lower()


@mcp.prompt()
async def voice_selector(args: VoiceSelectionPromptArgs) -> str:
    """Interactive guide for selecting the optimal voice for your content.

    Analyzes your requirements and recommends voices based on:
    - Content type (tutorial, podcast, audiobook, etc.)
    - Desired tone (professional, warm, casual, etc.)
    - Target audience
    - Content duration (affects quality tier recommendation)

    Provides:
    - Top 3 voice recommendations with rationale
    - Quality tier explanations (Premium/Professional/Good)
    - Speed recommendations for content type
    - Decision tree for quick selection

    Args:
        args: Content requirements (type, tone, audience, duration)

    Returns:
        Personalized voice selection guide

    Example:
        >>> await voice_selector(VoiceSelectionPromptArgs(
        ...     content_type="tutorial",
        ...     tone="professional",
        ...     audience="developers",
        ...     duration="medium"
        ... ))
    """
    try:
        bind_context(
            operation="voice_selector_prompt",
            content_type=args.content_type,
            tone=args.tone,
            duration=args.duration,
        )

        guide = mcp_utils.create_voice_selection_prompt(
            content_type=args.content_type,
            tone=args.tone,
            audience=args.audience,
            duration=args.duration,
        )

        log.info(
            "mcp_prompt_voice_selector_generated",
            content_type=args.content_type,
            tone=args.tone,
            audience=args.audience,
            duration=args.duration,
        )

        return guide

    except Exception as e:
        log.error("mcp_prompt_voice_selector_error", error=str(e))
        return f"❌ Error generating voice selection guide: {str(e)}"


class ScriptOptimizationPromptArgs(BaseModel):
    """Arguments for script optimization prompt."""

    target_audience: str = Field(default="general", description="Target audience for optimization")


@mcp.prompt()
async def script_optimizer(args: ScriptOptimizationPromptArgs) -> str:
    """Guide for optimizing scripts for natural-sounding TTS output.

    Provides comprehensive optimization techniques:
    - Sentence length and structure
    - Punctuation for natural pacing
    - Pronunciation handling (acronyms, numbers, technical terms)
    - Paragraph structuring for optimal token counts
    - Conversational style guidelines
    - Common TTS pitfalls to avoid

    Includes before/after examples and a complete optimization workflow.

    Args:
        args: Optimization parameters (target audience)

    Returns:
        Complete script optimization guide

    Example:
        >>> await script_optimizer(ScriptOptimizationPromptArgs(
        ...     target_audience="technical professionals"
        ... ))
    """
    try:
        bind_context(operation="script_optimizer_prompt", target_audience=args.target_audience)

        guide = mcp_utils.create_script_optimization_prompt(target_audience=args.target_audience)

        log.info("mcp_prompt_script_optimizer_generated", target_audience=args.target_audience)

        return guide

    except Exception as e:
        log.error("mcp_prompt_script_optimizer_error", error=str(e))
        return f"❌ Error generating script optimization guide: {str(e)}"


@mcp.prompt()
async def troubleshoot_tts() -> str:
    """Comprehensive troubleshooting guide for TTS quality issues.

    Covers common problems and solutions:
    - Robotic/unnatural voice
    - Mispronunciations
    - Pacing issues (too fast/slow)
    - Audio artifacts (clicks, pops)
    - Volume inconsistencies
    - Awkward pauses
    - Script length issues
    - Voice mismatches

    Includes diagnostic workflow and prevention checklist.

    Returns:
        Complete TTS troubleshooting guide

    Example:
        >>> await troubleshoot_tts()
    """
    try:
        bind_context(operation="troubleshoot_tts_prompt")

        guide = mcp_utils.create_troubleshooting_prompt()

        log.info("mcp_prompt_troubleshoot_tts_generated")

        return guide

    except Exception as e:
        log.error("mcp_prompt_troubleshoot_tts_error", error=str(e))
        return f"❌ Error generating troubleshooting guide: {str(e)}"
