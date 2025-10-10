# aparsoft_tts/mcp_server/mcp_tools_educational.py

"""Educational script processing tool for MCP.

This module provides a specialized tool for processing educational video scripts
that have segments with variable speeds. It automatically:
1. Parses markdown educational scripts
2. Extracts segments and their speed settings
3. Converts to podcast format with proper voice and speed per segment
4. Handles common educational script patterns

This prevents the common mistake of using process_script on markdown files
which would read all the formatting (###, metadata, etc.).
"""

import re
import warnings
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from aparsoft_tts.mcp_server.mcp_server_main import (
    mcp,
    config,
    get_tts_engine,
    PodcastSegment,
    GeneratePodcastRequest,
)

warnings.filterwarnings("ignore")

from aparsoft_tts.utils.logging import bind_context, get_logger

log = get_logger(__name__)


class ProcessEducationalScriptRequest(BaseModel):
    """Request model for process_educational_script tool."""

    script_path: str = Field(
        ..., description="Path to educational script markdown file"
    )
    output_path: str = Field(
        default="educational_voiceover.wav",
        description="Output audio file path"
    )
    voice: str = Field(
        default="hf_beta",
        description="Default voice to use (can be overridden per segment in script)"
    )
    default_speed: float = Field(
        default=1.1,
        description="Default speed if not specified in segment",
        ge=0.5,
        le=2.0
    )
    gap_duration: float = Field(
        default=0.5,
        description="Gap between segments in seconds",
        ge=0.0,
        le=5.0
    )
    enhance: bool = Field(
        default=True,
        description="Apply audio enhancement"
    )


def parse_educational_script(script_content: str, default_voice: str = "hf_beta", default_speed: float = 1.1) -> list[dict[str, Any]]:
    """Parse educational script markdown into segments.
    
    Recognizes patterns like:
    ## SEGMENT 1 - Title [Speed: 1.2x]
    Actual narration text here...
    
    Args:
        script_content: Raw markdown content
        default_voice: Default voice if not specified
        default_speed: Default speed if not specified in segment
        
    Returns:
        List of segment dictionaries with text, speed, voice, name
    """
    segments = []
    
    # Split by segment headers (## SEGMENT)
    segment_pattern = r'##\s+SEGMENT\s+(\d+)\s*[-–]\s*([^\[]+)(?:\[Speed:\s*([\d.]+)x\])?'
    
    # Find all segment headers and their positions
    matches = list(re.finditer(segment_pattern, script_content, re.IGNORECASE))
    
    for i, match in enumerate(matches):
        segment_num = match.group(1)
        segment_title = match.group(2).strip()
        speed_str = match.group(3)
        speed = float(speed_str) if speed_str else default_speed
        
        # Extract text between this segment and the next (or end)
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(script_content)
        
        segment_text = script_content[start_pos:end_pos].strip()
        
        # Clean up the text - remove markdown formatting
        # Remove lines that are just dashes or metadata
        lines = segment_text.split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            # Skip empty lines, lines with only dashes, or metadata lines
            if not line or line.startswith('---') or line.startswith('#'):
                continue
            # Skip lines that look like metadata (key: value)
            if ':' in line and len(line) < 100 and not any(hindi_char in line for hindi_char in 'अआइईउऊएऐओऔकखगघचछजझ'):
                continue
            clean_lines.append(line)
        
        # Join cleaned lines
        narration_text = ' '.join(clean_lines).strip()
        
        if narration_text:  # Only add if there's actual content
            segment_name = f"segment_{segment_num}_{segment_title.replace(' ', '_').lower()[:20]}"
            
            segments.append({
                'text': narration_text,
                'speed': speed,
                'voice': default_voice,
                'name': segment_name
            })
    
    return segments


@mcp.tool()
async def process_educational_script(request: ProcessEducationalScriptRequest) -> str:
    """Process educational video script with automatic segment parsing.
    
    **🎓 DESIGNED FOR EDUCATIONAL SCRIPTS!**
    
    This tool is specifically designed for educational video scripts that have:
    - Multiple segments with titles
    - Variable speed settings per segment (e.g., [Speed: 1.2x])
    - Markdown formatting
    - Metadata and headers
    
    **What it does:**
    ✅ Automatically parses markdown structure
    ✅ Extracts only narration text (ignores ###, metadata, etc.)
    ✅ Applies correct speed to each segment
    ✅ Creates podcast-style output with variable pacing
    ✅ Merges all segments into one audio file
    
    **When to use this tool:**
    - Educational video scripts with ## SEGMENT markers
    - Scripts with [Speed: X.Xx] annotations
    - Markdown files with narration text
    - YouTube tutorial voiceovers
    - Training videos with dynamic pacing
    
    **Example script format:**
    ```
    ## SEGMENT 1 - Introduction [Speed: 1.2x]
    Welcome to our tutorial! Today we'll learn...
    
    ## SEGMENT 2 - Main Content [Speed: 1.1x]
    Let's dive into the details...
    ```
    
    Args:
        request: Educational script processing parameters
        
    Returns:
        Success message with generated audio details
        
    Example:
        >>> await process_educational_script(ProcessEducationalScriptRequest(
        ...     script_path="tutorial_script.md",
        ...     voice="hf_beta",
        ...     output_path="tutorial_voiceover.wav"
        ... ))
    """
    try:
        bind_context(
            operation="process_educational_script",
            script_path=request.script_path
        )
        
        log.info(
            "mcp_process_educational_script_request",
            script_path=request.script_path,
            voice=request.voice,
            default_speed=request.default_speed
        )
        
        # Read script file
        script_path = Path(request.script_path)
        if not script_path.exists():
            return f"❌ Script file not found: {request.script_path}"
        
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # Parse segments
        parsed_segments = parse_educational_script(
            script_content,
            default_voice=request.voice,
            default_speed=request.default_speed
        )
        
        if not parsed_segments:
            return f"❌ No segments found in script. Check format (should have ## SEGMENT markers)"
        
        log.info(
            "mcp_educational_script_parsed",
            num_segments=len(parsed_segments),
            script_path=request.script_path
        )
        
        # Convert to PodcastSegment objects
        podcast_segments = [
            PodcastSegment(
                text=seg['text'],
                voice=seg['voice'],
                speed=seg['speed'],
                name=seg['name']
            )
            for seg in parsed_segments
        ]
        
        # Create podcast request
        podcast_request = GeneratePodcastRequest(
            segments=podcast_segments,
            output_path=request.output_path,
            gap_duration=request.gap_duration,
            enhance=request.enhance
        )
        
        # Import the generate_podcast function
        from aparsoft_tts.mcp_server.mcp_tools import generate_podcast
        
        # Generate podcast
        result = await generate_podcast(podcast_request)
        
        log.info(
            "mcp_educational_script_processed",
            num_segments=len(parsed_segments),
            output_path=request.output_path
        )
        
        # Enhance result message
        enhanced_result = f"""🎓 Educational Script Processed Successfully!

📚 SCRIPT ANALYSIS:
Script: {Path(request.script_path).name}
Segments Found: {len(parsed_segments)}
Voice: {request.voice}
Speed Range: {min(s['speed'] for s in parsed_segments):.2f}x - {max(s['speed'] for s in parsed_segments):.2f}x

{result}

💡 TIP: This tool automatically parsed your markdown script and extracted
only the narration text, ignoring all formatting and metadata!
"""
        
        return enhanced_result
        
    except Exception as e:
        log.error("mcp_process_educational_script_error", error=str(e))
        return f"❌ Error processing educational script: {str(e)}"
