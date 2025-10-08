# aparsoft_tts/mcp_server/mcp_utils.py

"""MCP Resources and Prompts for Aparsoft TTS Server.

This module provides:
1. Resources - Read-only data sources for voice information, presets, etc.
2. Prompts - Guided workflows for podcast creation, voice selection, etc.

Resources help Claude make informed decisions by providing context.
Prompts guide users through complex workflows with best practices.
"""

import json
from pathlib import Path
from typing import Any

from aparsoft_tts.config import get_config
from aparsoft_tts.core.engine import ALL_VOICES, FEMALE_VOICES, MALE_VOICES
from aparsoft_tts.utils.logging import get_logger

log = get_logger(__name__)
config = get_config()

# Voice Characteristics Database
# Based on Kokoro-82M voice quality grades and training data
# Source: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
VOICE_CHARACTERISTICS = {
    # American Male Voices
    "am_michael": {
        "name": "Michael",
        "gender": "Male",
        "accent": "American",
        "quality_grade": "B",
        "training_hours": "H (1-10 hours)",
        "overall_grade": "C+",
        "characteristics": [
            "Professional and authoritative",
            "Deeper tones with clear articulation",
            "Reliable for technical content",
            "Moderate inflection range",
        ],
        "best_for": [
            "YouTube tutorials and educational content",
            "Professional presentations",
            "Technical documentation voiceovers",
            "Business and corporate content",
            "News-style narration",
        ],
        "avoid_for": [
            "Highly emotional or dramatic content",
            "Children's content",
            "Very casual conversational podcasts",
        ],
        "speed_recommendations": {
            "tutorial": {"speed": 0.95, "reason": "Clear instruction delivery"},
            "podcast": {"speed": 1.0, "reason": "Natural conversational pace"},
            "announcement": {"speed": 1.05, "reason": "Energetic delivery"},
            "meditation": {"speed": 0.85, "reason": "Calm, soothing pace"},
        },
        "sample_texts": [
            "Welcome to today's tutorial on artificial intelligence and machine learning.",
            "In this video, we'll explore the fundamentals of neural networks.",
            "Let's dive into the technical details and see how this works in practice.",
        ],
        "voice_sha256": "9a443b79",
    },
    "am_adam": {
        "name": "Adam",
        "gender": "Male",
        "accent": "American",
        "quality_grade": "D",
        "training_hours": "H (1-10 hours)",
        "overall_grade": "F+",
        "characteristics": [
            "Natural inflection patterns",
            "Casual and approachable tone",
            "Variable quality (lower grade)",
            "Less refined than other voices",
        ],
        "best_for": [
            "Casual vlogs and personal content",
            "Informal updates and announcements",
            "Quick prototypes and tests",
        ],
        "avoid_for": [
            "Professional or corporate content",
            "Long-form narration",
            "High-quality productions",
        ],
        "speed_recommendations": {
            "casual": {"speed": 1.0, "reason": "Natural everyday speech"},
            "vlog": {"speed": 1.05, "reason": "Energetic personal delivery"},
        },
        "sample_texts": [
            "Hey everyone, welcome back to my channel!",
            "Today I want to share something really cool with you.",
        ],
        "voice_sha256": "ced7e284",
    },
    # British Male Voices
    "bm_george": {
        "name": "George",
        "gender": "Male",
        "accent": "British",
        "quality_grade": "B",
        "training_hours": "MM (10-100 minutes)",
        "overall_grade": "C",
        "characteristics": [
            "Classic British accent",
            "Authoritative and distinguished",
            "Clear enunciation",
            "Professional demeanor",
        ],
        "best_for": [
            "Documentary narration",
            "Historical content",
            "British audience content",
            "Literary audiobooks",
            "Formal presentations",
        ],
        "avoid_for": [
            "American-targeted casual content",
            "Hip modern vlogs",
            "Children's entertainment",
        ],
        "speed_recommendations": {
            "documentary": {"speed": 0.95, "reason": "Measured, authoritative delivery"},
            "audiobook": {"speed": 1.0, "reason": "Natural reading pace"},
            "presentation": {"speed": 1.0, "reason": "Professional clarity"},
        },
        "sample_texts": [
            "Throughout history, we have witnessed remarkable transformations.",
            "Let us examine the evidence from a historical perspective.",
            "This brings us to our next point of consideration.",
        ],
        "voice_sha256": "f1bc8122",
    },
    "bm_lewis": {
        "name": "Lewis",
        "gender": "Male",
        "accent": "British",
        "quality_grade": "C",
        "training_hours": "H (1-10 hours)",
        "overall_grade": "D+",
        "characteristics": [
            "Modern British accent",
            "Approachable and contemporary",
            "Less formal than George",
            "Moderate quality",
        ],
        "best_for": [
            "Modern British content",
            "Contemporary podcasts",
            "Tech reviews with British flair",
            "Casual educational content",
        ],
        "avoid_for": ["Highly formal content", "Classical narration", "Very long productions"],
        "speed_recommendations": {
            "podcast": {"speed": 1.05, "reason": "Modern conversational energy"},
            "review": {"speed": 1.0, "reason": "Clear product discussion"},
        },
        "sample_texts": [
            "Right, let's have a look at what makes this interesting.",
            "I've been using this for a while now, and here's what I think.",
        ],
        "voice_sha256": "b5204750",
    },
    # American Female Voices
    "af_bella": {
        "name": "Bella",
        "gender": "Female",
        "accent": "American",
        "quality_grade": "A",
        "training_hours": "HH (10-100 hours)",
        "overall_grade": "A-",
        "characteristics": [
            "Warm and inviting tones",
            "High quality (top-tier voice)",
            "Excellent for emotional content",
            "Natural expressiveness",
            "Wide dynamic range",
        ],
        "best_for": [
            "Podcast hosting (warm, engaging)",
            "Storytelling and narratives",
            "Lifestyle and wellness content",
            "Customer-facing communications",
            "Audiobooks with emotional depth",
            "Brand voiceovers requiring warmth",
        ],
        "avoid_for": [
            "Highly technical/dry content",
            "News-style reporting",
            "Formal business presentations",
        ],
        "speed_recommendations": {
            "podcast": {"speed": 1.0, "reason": "Natural, warm conversation"},
            "storytelling": {"speed": 0.95, "reason": "Engaging narrative pace"},
            "announcement": {"speed": 1.05, "reason": "Friendly energy"},
            "meditation": {"speed": 0.85, "reason": "Soothing, calming tone"},
        },
        "sample_texts": [
            "Welcome to our podcast where we explore the stories that matter.",
            "Today, I'm excited to share something that really changed my perspective.",
            "Let me tell you about a journey that transformed everything.",
        ],
        "voice_sha256": "8cb64e02",
        "special_notes": "🔥 Premium quality - Highest grade female voice available",
    },
    "af_sarah": {
        "name": "Sarah",
        "gender": "Female",
        "accent": "American",
        "quality_grade": "B",
        "training_hours": "H (1-10 hours)",
        "overall_grade": "C+",
        "characteristics": [
            "Clear and articulate",
            "Professional and polished",
            "Excellent pronunciation",
            "Balanced tone",
        ],
        "best_for": [
            "Professional presentations",
            "E-learning and training",
            "Corporate communications",
            "Product demonstrations",
            "Educational YouTube content",
        ],
        "avoid_for": [
            "Very casual or intimate content",
            "Entertainment or comedy",
            "Dramatic storytelling",
        ],
        "speed_recommendations": {
            "tutorial": {"speed": 0.95, "reason": "Clear educational delivery"},
            "presentation": {"speed": 1.0, "reason": "Professional clarity"},
            "announcement": {"speed": 1.0, "reason": "Polished delivery"},
        },
        "sample_texts": [
            "In this training module, we will cover the essential concepts.",
            "Let's begin by examining the key features of this platform.",
            "This process involves three important steps.",
        ],
        "voice_sha256": "49bd364e",
    },
    "af_nicole": {
        "name": "Nicole",
        "gender": "Female",
        "accent": "American",
        "quality_grade": "B",
        "training_hours": "HH (10-100 hours)",
        "overall_grade": "B-",
        "characteristics": [
            "Dynamic vocal range",
            "Versatile expression",
            "Moderate to high quality",
            "Adaptable to various contexts",
        ],
        "best_for": [
            "Versatile content needs",
            "Mixed content types",
            "Podcasts with varied topics",
            "Multi-purpose voiceovers",
            "Character narration",
        ],
        "avoid_for": ["Content requiring very specific tone", "Ultra-professional corporate use"],
        "speed_recommendations": {
            "varied_content": {"speed": 1.0, "reason": "Flexible baseline"},
            "energetic": {"speed": 1.1, "reason": "Dynamic delivery"},
            "calm": {"speed": 0.95, "reason": "Measured pace"},
        },
        "sample_texts": [
            "From tech to lifestyle, we cover it all on this show.",
            "Each episode brings you something different and exciting.",
        ],
        "voice_sha256": "c5561808",
        "special_notes": "🎧 Versatile - Good for diverse content types",
    },
    "af_sky": {
        "name": "Sky",
        "gender": "Female",
        "accent": "American",
        "quality_grade": "B",
        "training_hours": "M (1-10 minutes) 🤏",
        "overall_grade": "C-",
        "characteristics": [
            "Youthful and energetic",
            "Bright and upbeat",
            "Less training data (use cautiously)",
            "Modern and casual",
        ],
        "best_for": [
            "Youth-oriented content",
            "Upbeat announcements",
            "Short energetic segments",
            "Social media voiceovers",
        ],
        "avoid_for": [
            "Long-form content",
            "Professional/serious topics",
            "Technical documentation",
        ],
        "speed_recommendations": {
            "energetic": {"speed": 1.1, "reason": "Youthful enthusiasm"},
            "casual": {"speed": 1.05, "reason": "Bright delivery"},
        },
        "sample_texts": [
            "Hey guys! Check out this amazing update!",
            "This is so cool, you're going to love it!",
        ],
        "voice_sha256": "c799548a",
        "special_notes": "⚠️ Limited training data - best for short content",
    },
    # British Female Voices
    "bf_emma": {
        "name": "Emma",
        "gender": "Female",
        "accent": "British",
        "quality_grade": "B",
        "training_hours": "HH (10-100 hours)",
        "overall_grade": "B-",
        "characteristics": [
            "Professional British accent",
            "Clear and articulate",
            "Formal and polished",
            "High quality training",
        ],
        "best_for": [
            "British professional content",
            "Corporate presentations (UK)",
            "Educational content for British audience",
            "Formal announcements",
            "Professional podcasts",
        ],
        "avoid_for": [
            "Very casual American content",
            "Intimate storytelling",
            "Children's entertainment",
        ],
        "speed_recommendations": {
            "professional": {"speed": 1.0, "reason": "Clear professional delivery"},
            "formal": {"speed": 0.95, "reason": "Measured, authoritative pace"},
        },
        "sample_texts": [
            "Welcome to this professional development session.",
            "We shall now proceed to the next item on our agenda.",
            "This analysis demonstrates several key findings.",
        ],
        "voice_sha256": "d0a423de",
    },
    "bf_isabella": {
        "name": "Isabella",
        "gender": "Female",
        "accent": "British",
        "quality_grade": "B",
        "training_hours": "MM (10-100 minutes)",
        "overall_grade": "C",
        "characteristics": [
            "Soft and gentle tones",
            "Approachable British accent",
            "Warm delivery",
            "Less formal than Emma",
        ],
        "best_for": [
            "Gentle narration",
            "Wellness and meditation content",
            "Soft-spoken British content",
            "Bedtime stories or audiobooks",
            "Calm instructional content",
        ],
        "avoid_for": [
            "High-energy content",
            "Formal business presentations",
            "Technical specifications",
        ],
        "speed_recommendations": {
            "narration": {"speed": 0.95, "reason": "Gentle storytelling"},
            "meditation": {"speed": 0.85, "reason": "Calm, soothing pace"},
            "casual": {"speed": 1.0, "reason": "Soft conversation"},
        },
        "sample_texts": [
            "Let's take a moment to relax and breathe deeply.",
            "I'd like to share a story that brought me peace.",
            "Gently close your eyes and listen to these words.",
        ],
        "voice_sha256": "cdd4c370",
    },
    # Special Voice
    "af": {
        "name": "Bella-Sarah Mix",
        "gender": "Female",
        "accent": "American",
        "quality_grade": "A/B",
        "training_hours": "Combined (HH + H hours)",
        "overall_grade": "A-/C+",
        "characteristics": [
            "50-50 mix of Bella and Sarah",
            "Combines warmth with clarity",
            "Balanced expressiveness and professionalism",
            "Good all-purpose voice",
        ],
        "best_for": [
            "General-purpose content",
            "Mixed content types",
            "When you can't decide between warm/professional",
            "Versatile applications",
        ],
        "avoid_for": [
            "Content requiring very specific tone",
            "When consistency with single voice is critical",
        ],
        "speed_recommendations": {
            "general": {"speed": 1.0, "reason": "Balanced delivery"},
            "professional": {"speed": 0.95, "reason": "Clear but warm"},
            "engaging": {"speed": 1.05, "reason": "Friendly energy"},
        },
        "sample_texts": [
            "Welcome! Today we're exploring something fascinating.",
            "Let me walk you through this in a clear and friendly way.",
        ],
        "special_notes": "🎭 Hybrid voice - combines best of both Bella and Sarah",
    },
}

# Configuration Presets for Common Use Cases
CONFIGURATION_PRESETS = {
    "youtube_tutorial": {
        "name": "YouTube Tutorial",
        "description": "Professional educational content with clear delivery",
        "recommended_voices": ["am_michael", "af_sarah"],
        "settings": {
            "voice": "am_michael",
            "speed": 0.95,
            "enhance": True,
            "gap_duration": 0.5,
            "trim_silence": True,
        },
        "tips": [
            "Use slower speed (0.95) for clarity",
            "Enable audio enhancement for professional quality",
            "Add gaps between sections for natural pacing",
            "Consider am_michael for tech content or af_sarah for general education",
        ],
    },
    "podcast_host": {
        "name": "Podcast Host",
        "description": "Warm, engaging conversational podcasts",
        "recommended_voices": ["af_bella", "af_nicole", "am_michael"],
        "settings": {
            "voice": "af_bella",
            "speed": 1.0,
            "enhance": True,
            "gap_duration": 0.4,
            "podcast_default_gap": 0.6,
        },
        "tips": [
            "Use af_bella for warmth or am_michael for authority",
            "Natural conversational speed (1.0)",
            "Shorter gaps (0.4s) for dynamic feel",
            "ALWAYS include AI disclosure in first segment (legal requirement)",
        ],
    },
    "audiobook_narration": {
        "name": "Audiobook Narration",
        "description": "Long-form storytelling and narrative content",
        "recommended_voices": ["af_bella", "bm_george", "af_sarah"],
        "settings": {
            "voice": "af_bella",
            "speed": 1.0,
            "enhance": True,
            "gap_duration": 0.8,
            "trim_silence": True,
        },
        "tips": [
            "Choose voice matching content tone (af_bella for warm stories, bm_george for historical)",
            "Standard speed for natural reading",
            "Longer gaps between chapters/sections",
            "Process in smaller chunks for better quality",
        ],
    },
    "meditation_guide": {
        "name": "Meditation/Wellness Guide",
        "description": "Calm, soothing guidance for relaxation",
        "recommended_voices": ["bf_isabella", "af_bella"],
        "settings": {
            "voice": "bf_isabella",
            "speed": 0.85,
            "enhance": True,
            "gap_duration": 1.0,
            "trim_silence": False,
        },
        "tips": [
            "Slow speed (0.85) for calming effect",
            "Longer gaps for breathing space",
            "bf_isabella's soft tones ideal for meditation",
            "Keep trim_silence minimal to preserve atmosphere",
        ],
    },
    "news_announcement": {
        "name": "News/Announcement",
        "description": "Professional news-style delivery",
        "recommended_voices": ["am_michael", "af_sarah", "bm_george"],
        "settings": {
            "voice": "am_michael",
            "speed": 1.0,
            "enhance": True,
            "gap_duration": 0.3,
            "trim_silence": True,
        },
        "tips": [
            "Professional voices with authority",
            "Standard speed for news delivery",
            "Short gaps for continuous flow",
            "Clear articulation critical",
        ],
    },
    "casual_vlog": {
        "name": "Casual Vlog",
        "description": "Personal, casual YouTube vlogs",
        "recommended_voices": ["af_sky", "am_adam", "af_nicole"],
        "settings": {"voice": "af_sky", "speed": 1.05, "enhance": True, "gap_duration": 0.3},
        "tips": [
            "Slightly faster speed for energy",
            "Youth-oriented voices (af_sky, am_adam)",
            "Short gaps for dynamic pacing",
            "Keep it conversational and light",
        ],
    },
    "product_demo": {
        "name": "Product Demonstration",
        "description": "Professional product showcases and demos",
        "recommended_voices": ["af_sarah", "am_michael"],
        "settings": {"voice": "af_sarah", "speed": 0.95, "enhance": True, "gap_duration": 0.5},
        "tips": [
            "Clear articulation for feature descriptions",
            "Slightly slower for comprehension",
            "Professional tone builds trust",
            "Pause between features for emphasis",
        ],
    },
    "documentary_narration": {
        "name": "Documentary Narration",
        "description": "Authoritative documentary voiceover",
        "recommended_voices": ["bm_george", "am_michael"],
        "settings": {"voice": "bm_george", "speed": 0.95, "enhance": True, "gap_duration": 0.7},
        "tips": [
            "bm_george brings gravitas and authority",
            "Measured pace for impactful delivery",
            "Longer gaps for dramatic effect",
            "Perfect for historical/nature documentaries",
        ],
    },
}


def get_voice_info_resource(voice_id: str) -> dict[str, Any]:
    """Get detailed information resource for a specific voice.

    Args:
        voice_id: Voice identifier (e.g., 'am_michael')

    Returns:
        Dictionary containing voice information formatted as MCP resource
    """
    if voice_id not in VOICE_CHARACTERISTICS:
        return {
            "error": f"Voice '{voice_id}' not found",
            "available_voices": list(VOICE_CHARACTERISTICS.keys()),
            "uri": f"tts://voice/info/{voice_id}",
        }

    info = VOICE_CHARACTERISTICS[voice_id]

    return {
        "uri": f"tts://voice/info/{voice_id}",
        "name": f"{info['name']} Voice Information",
        "mimeType": "application/json",
        "voice_id": voice_id,
        "details": info,
    }


def get_all_voices_comparison() -> dict[str, Any]:
    """Get comparison of all voices organized by category.

    Returns:
        Dictionary containing comprehensive voice comparison
    """
    comparison = {
        "uri": "tts://voices/comparison",
        "name": "Voice Comparison Guide",
        "mimeType": "application/json",
        "total_voices": len(ALL_VOICES),
        "categories": {
            "premium_quality": {
                "description": "Highest quality voices (Grade A or B with HH hours training)",
                "voices": [],
            },
            "professional": {
                "description": "Reliable professional voices (Grade B or C+)",
                "voices": [],
            },
            "casual": {"description": "Good for casual content (Grade C to D)", "voices": []},
            "by_gender": {"male": MALE_VOICES, "female": FEMALE_VOICES},
            "by_accent": {
                "american": [v for v in ALL_VOICES if v.startswith(("am_", "af_"))],
                "british": [v for v in ALL_VOICES if v.startswith(("bm_", "bf_"))],
            },
        },
        "voice_details": {},
    }

    # Categorize voices by quality
    for voice_id, info in VOICE_CHARACTERISTICS.items():
        grade = info.get("overall_grade", "")

        if "A" in grade or (grade.startswith("B") and "HH" in info.get("training_hours", "")):
            comparison["categories"]["premium_quality"]["voices"].append(voice_id)
        elif grade.startswith(("B", "C+")):
            comparison["categories"]["professional"]["voices"].append(voice_id)
        else:
            comparison["categories"]["casual"]["voices"].append(voice_id)

        # Add abbreviated voice details
        comparison["voice_details"][voice_id] = {
            "name": info["name"],
            "gender": info["gender"],
            "accent": info["accent"],
            "grade": info["overall_grade"],
            "primary_use": info["best_for"][0] if info["best_for"] else "General",
        }

    return comparison


def get_preset_resource(preset_name: str) -> dict[str, Any]:
    """Get configuration preset for a specific use case.

    Args:
        preset_name: Preset identifier (e.g., 'youtube_tutorial')

    Returns:
        Dictionary containing preset configuration
    """
    if preset_name not in CONFIGURATION_PRESETS:
        return {
            "error": f"Preset '{preset_name}' not found",
            "available_presets": list(CONFIGURATION_PRESETS.keys()),
            "uri": f"tts://presets/{preset_name}",
        }

    preset = CONFIGURATION_PRESETS[preset_name]

    return {
        "uri": f"tts://presets/{preset_name}",
        "name": preset["name"],
        "mimeType": "application/json",
        "preset": preset,
    }


def get_all_presets() -> dict[str, Any]:
    """Get all available configuration presets.

    Returns:
        Dictionary containing all presets organized by category
    """
    return {
        "uri": "tts://presets/all",
        "name": "All Configuration Presets",
        "mimeType": "application/json",
        "presets": CONFIGURATION_PRESETS,
        "categories": {
            "education": ["youtube_tutorial", "audiobook_narration"],
            "entertainment": ["podcast_host", "casual_vlog", "documentary_narration"],
            "professional": ["news_announcement", "product_demo"],
            "wellness": ["meditation_guide"],
        },
    }


# Prompt Templates
def create_podcast_prompt(
    topic: str, duration_minutes: int = 10, num_hosts: int = 2, style: str = "conversational"
) -> str:
    """Generate guided podcast creation prompt.

    Args:
        topic: Podcast topic
        duration_minutes: Target duration in minutes
        num_hosts: Number of hosts/speakers
        style: Podcast style (conversational, interview, educational)

    Returns:
        Formatted prompt template
    """
    segments_estimate = (duration_minutes * 60) // 20  # ~20 seconds per segment

    return f"""🎙️ **PODCAST CREATION GUIDE**

**Project:** {topic}
**Duration:** {duration_minutes} minutes (~{segments_estimate} segments)
**Hosts:** {num_hosts}
**Style:** {style}

---

### ⚠️ STEP 1: MANDATORY AI DISCLOSURE (LEGAL REQUIREMENT)

Your **FIRST segment MUST include AI disclosure**. This is required by:
- Apple Podcasts guidelines
- YouTube ToS for AI-generated content
- Spotify recommendations
- Ethical AI practices

**Example disclosure:**
"Welcome to [Podcast Name]. Before we begin, we want to be transparent: this podcast is created using Claude by Anthropic for content creation and Aparsoft TTS powered by Kokoro-82M for voice synthesis."

**Do NOT skip this step** - it's both a legal and ethical requirement.

---

### STEP 2: STRUCTURE YOUR CONTENT ({segments_estimate} segments recommended)

**Opening (2-3 segments):**
1. AI Disclosure (mandatory)
2. Welcome & intro music mention
3. Topic tease: "Today we're exploring {topic}..."

**Main Content ({segments_estimate - 6} segments):**
- Break {topic} into 3-5 key discussion points
- Each point: 3-5 segments of dialogue
- Use **dialogue format**, NOT monologue:
  ✅ "What do you think about X?" / "Really?" / "That's huge!"
  ❌ Long uninterrupted speeches

**Closing (2-3 segments):**
1. Summary of key points
2. Call to action (subscribe, visit website)
3. Thank you & outro

---

### STEP 3: VOICE & SPEED SELECTION

**{style.capitalize()} Style Recommendations:**

**Option 1: Warm & Engaging**
- Host 1: `af_bella` at 1.0x (warm, main host)
- Host 2: `am_michael` at 1.05x (professional co-host)

**Option 2: Professional Authority**
- Host 1: `am_michael` at 1.0x (authoritative lead)
- Host 2: `af_sarah` at 1.0x (clear co-host)

**Option 3: British Flair**
- Host 1: `bm_george` at 0.95x (distinguished)
- Host 2: `bf_emma` at 1.0x (professional)

**Speed Guidelines:**
- 0.95-1.0x: Important info, disclosure, key points
- 1.0-1.05x: Normal conversation flow
- 1.1-1.2x: Excitement, reveals, "Really?!" reactions
- 0.90-0.95x: Thoughtful moments, emphasizing importance

---

### STEP 4: WRITING NATURAL DIALOGUE

✅ **DO:**
- Keep segments SHORT (15-40 words each)
- Ask questions: "What makes this interesting?"
- React naturally: "Really?" "Exactly!" "That's fascinating!"
- Use contractions: "it's" not "it is", "we're" not "we are"
- Vary sentence length: mix short reactions with explanations
- Include verbal ticks: "you know", "I mean", "right?"

❌ **DON'T:**
- Write long monologues (sounds robotic!)
- Use overly formal language
- Forget to switch between hosts
- Use same speed for everything
- Write like a news script

---

### STEP 5: EXAMPLE STRUCTURE

Here's how your segments might look:

```json
[
  {{
    "text": "Welcome to Tech Insights. Before we dive in, full transparency: this podcast is created using Claude AI and Aparsoft TTS.",
    "voice": "af_bella",
    "speed": 1.0,
    "name": "mandatory_disclosure"
  }},
  {{
    "text": "Thanks Sarah! I'm really excited about today's topic.",
    "voice": "am_michael",
    "speed": 1.05,
    "name": "host_intro"
  }},
  {{
    "text": "Me too! So what's the big story?",
    "voice": "af_bella",
    "speed": 1.1,
    "name": "excited_question"
  }},
  {{
    "text": "Well, let me tell you...",
    "voice": "am_michael",
    "speed": 1.0,
    "name": "transition"
  }}
]
```

---

### TECHNICAL SETTINGS

**Gap Duration:** 0.4-0.6 seconds (shorter = more dynamic)
**Enhancement:** Always enable for professional quality
**Segment Count:** 15-25 segments for {duration_minutes} minutes
**Max Segment Length:** Keep under 250 tokens for best quality

---

**Ready to create your podcast?** 

Tell me more about "{topic}" and I'll help you structure the perfect episode with:
1. AI disclosure (done right)
2. Natural dialogue flow
3. Optimal voice assignments
4. Engaging conversation structure
5. Professional pacing

Let's make something great! 🎧
"""


def create_voice_selection_prompt(
    content_type: str,
    tone: str = "professional",
    audience: str = "adults",
    duration: str = "medium",
) -> str:
    """Generate voice selection guidance prompt.

    Args:
        content_type: Type of content (tutorial, podcast, audiobook, etc.)
        tone: Desired tone (professional, casual, warm, authoritative)
        audience: Target audience
        duration: Content duration (short, medium, long)

    Returns:
        Formatted voice selection guide
    """
    return f"""🎤 **VOICE SELECTION ASSISTANT**

**Content Type:** {content_type}
**Desired Tone:** {tone}
**Target Audience:** {audience}
**Duration:** {duration}

---

### UNDERSTANDING YOUR NEEDS

Let me help you find the perfect voice by analyzing your requirements:

**1. Content Type Analysis: {content_type}**

Common voice choices for this type:
- **Tutorial/Educational:** am_michael, af_sarah (clear, authoritative)
- **Podcast:** af_bella, af_nicole, am_michael (warm, engaging)
- **Audiobook:** af_bella, bm_george (expressive, storytelling)
- **News/Announcement:** am_michael, af_sarah, bm_george (professional)
- **Meditation/Wellness:** bf_isabella, af_bella (soft, calming)
- **Vlog/Casual:** af_sky, am_adam, af_nicole (energetic, approachable)

**2. Tone Matching: {tone}**

Best voices for "{tone}" tone:
- **Professional:** am_michael, af_sarah, bf_emma, bm_george
- **Warm:** af_bella, bf_isabella
- **Authoritative:** bm_george, am_michael
- **Casual:** af_sky, am_adam, af_nicole
- **Energetic:** af_sky, af_nicole

**3. Duration Considerations: {duration}**

- **Short (<5 min):** Any voice works, consider energy level
- **Medium (5-20 min):** Choose voices with good quality grades (B or above)
- **Long (>20 min):** PREMIUM voices recommended:
  - af_bella (A- grade, HH hours training) ⭐ BEST
  - af_nicole (B- grade, HH hours training)
  - bf_emma (B- grade, HH hours training)

---

### TOP RECOMMENDATIONS

Based on your needs, here are my top 3 suggestions:

**Option 1: {get_voice_recommendation(content_type, tone, 1)}**
**Option 2: {get_voice_recommendation(content_type, tone, 2)}**
**Option 3: {get_voice_recommendation(content_type, tone, 3)}**

---

### VOICE QUALITY GUIDE

**🔥 PREMIUM TIER (Highest Quality):**
- `af_bella` - American Female (A- grade, HH hours) - WARMEST
- `af_nicole` - American Female (B- grade, HH hours) - VERSATILE
- `bf_emma` - British Female (B- grade, HH hours) - PROFESSIONAL

**⭐ PROFESSIONAL TIER (Reliable):**
- `am_michael` - American Male (C+ grade) - AUTHORITATIVE
- `af_sarah` - American Female (C+ grade) - CLEAR
- `bm_george` - British Male (C grade) - DISTINGUISHED

**👍 GOOD TIER (Casual Content):**
- `af_sky` - American Female (C- grade) - ENERGETIC
- `am_adam` - American Male (F+ grade) - CASUAL
- Other voices - Good for specific use cases

---

### SPEED RECOMMENDATIONS

For {content_type}:

- **Educational/Tutorial:** 0.95x (clear, easy to follow)
- **Podcast/Conversation:** 1.0-1.05x (natural pace)
- **Excitement/Announcement:** 1.1-1.2x (energetic)
- **Meditation/Calm:** 0.85-0.90x (soothing)
- **Audiobook:** 1.0x (standard reading pace)

---

### QUICK DECISION TREE

**Can't decide? Answer these:**

1. **Need warmth & emotion?** → `af_bella`
2. **Need professional authority?** → `am_michael` or `bm_george`
3. **Need clear, neutral delivery?** → `af_sarah`
4. **Need British accent?** → `bm_george` (male) or `bf_emma` (female)
5. **Making a casual vlog?** → `af_sky` or `am_adam`
6. **Long content (>30 min)?** → `af_bella` (premium quality essential)

---

### NEXT STEPS

Would you like me to:
A) **Generate sample text** with your top choice to hear it first
B) **Compare 2-3 voices** side-by-side with the same text
C) **See detailed characteristics** of a specific voice
D) **Proceed with generation** using recommended voice

**Or tell me more about your specific content and I'll refine these suggestions!**

Remember: You can always test different voices quickly. The beauty of TTS is experimentation costs nothing! 🎯
"""

    def _get_voice_recommendation(self, content_type: str, tone: str, rank: int) -> str:
        """Internal helper to get voice recommendations."""
        # This is a simplified helper - in practice, you'd have more complex logic
        recommendations = {
            "tutorial": ["am_michael", "af_sarah", "af_bella"],
            "podcast": ["af_bella", "am_michael", "af_nicole"],
            "audiobook": ["af_bella", "bm_george", "af_nicole"],
        }
        default = ["af_bella", "am_michael", "af_sarah"]
        voices = recommendations.get(content_type.lower(), default)

        if rank <= len(voices):
            voice_id = voices[rank - 1]
            info = VOICE_CHARACTERISTICS.get(voice_id, {})
            return f"`{voice_id}` - {info.get('characteristics', [''])[0]}"
        return "af_bella - Warm and versatile"


def create_script_optimization_prompt(target_audience: str = "general") -> str:
    """Generate script optimization guidance prompt.

    Args:
        target_audience: Target audience for optimization

    Returns:
        Formatted optimization guide
    """
    return f"""📝 **SCRIPT OPTIMIZATION FOR TTS**

**Target Audience:** {target_audience}

---

### WHY OPTIMIZE FOR TTS?

TTS engines work best with well-structured text. Optimizing your script ensures:
- ✅ Natural-sounding delivery
- ✅ Proper pacing and pauses
- ✅ Clear pronunciation
- ✅ Better listener comprehension

---

### OPTIMIZATION CHECKLIST

**1. SENTENCE LENGTH** ✂️
- ❌ Avoid: Long run-on sentences (>30 words)
- ✅ Do: Break into shorter sentences (10-20 words ideal)
- Why: Better breath points, clearer delivery

**Example:**
❌ "This tutorial covers advanced techniques in machine learning including neural networks deep learning algorithms and various optimization strategies that you can apply to your projects."

✅ "This tutorial covers advanced machine learning techniques. We'll explore neural networks and deep learning algorithms. You'll also learn optimization strategies for your projects."

---

**2. PUNCTUATION FOR PACING** ⏸️
- Use periods for full stops
- Use commas for brief pauses
- Use ellipsis (...) for longer pauses
- Use dashes (—) for dramatic pauses

**Example:**
"Machine learning is powerful... but it requires practice. The basics — once mastered — open endless possibilities."

---

**3. PRONUNCIATION CONCERNS** 🗣️
- Spell out acronyms on first use: "AI (Artificial Intelligence)"
- Use hyphens for clarity: "re-evaluate" not "reevaluate"
- Write numbers as words for important ones: "three key points"
- Avoid special characters that might confuse: use "and" not "&"

**Watch out for:**
- Technical jargon (spell phonetically if needed)
- Brand names (verify pronunciation)
- Foreign words (anglicize or avoid)

---

**4. PARAGRAPH STRUCTURE** 📄
- One main idea per paragraph
- Leave blank lines between paragraphs
- Each paragraph = one audio segment
- Aim for 100-250 tokens per paragraph (optimal TTS range)

---

**5. CONVERSATIONAL STYLE** 💬
- Use contractions: "we'll" not "we will"
- Include natural transitions: "Now," "Next," "First," "Finally,"
- Ask rhetorical questions: "Why does this matter?"
- Address listener directly: "you" not "one"

❌ Formal: "One must consider the implications."
✅ Conversational: "You should think about what this means."

---

**6. EMPHASIS AND TONE** 🎯
- Use ALL CAPS sparingly for emphasis: "This is CRITICAL"
- Italics work in some contexts: use _ or * in markdown
- Repeat for emphasis: "very, very important"
- Short sentences for impact: "Listen carefully. This matters."

---

**7. AVOID THESE TTS PITFALLS** ⚠️

❌ Web URLs: "double-u double-u double-u dot..."
   ✅ Say: "visit our website at example dot com"

❌ Symbols: "@, #, &, %, $"
   ✅ Spell out: "at, hashtag, and, percent, dollars"

❌ Lists without pauses: "Item1item2item3"
   ✅ Format clearly:
   ```
   Here are three items:
   First, item one.
   Second, item two.
   Finally, item three.
   ```

❌ All caps screaming: "THIS IS IMPORTANT"
   ✅ Better: "This is really important."

---

### OPTIMIZATION WORKFLOW

**Step 1: Read Aloud**
- Does it sound natural when YOU read it?
- Mark awkward phrases

**Step 2: Check Sentence Length**
- Count words per sentence
- Break up anything >30 words

**Step 3: Add Punctuation Pauses**
- Where do YOU naturally pause?
- Add commas, periods, ellipsis

**Step 4: Test a Sample**
- Generate one paragraph
- Listen critically
- Adjust as needed

**Step 5: Apply Learning**
- Fix similar issues throughout
- Maintain consistent style

---

### KOKORO-SPECIFIC TIPS

**Token Limits:**
- Optimal: 100-250 tokens per segment
- Maximum: 450 tokens (quality degrades beyond this)
- Auto-chunking: Script will be split if too long

**Quality Sweet Spot:**
- 15-25 segments for 10-minute content
- Each segment: 15-40 words
- Natural breaks at paragraphs

---

### EXAMPLE TRANSFORMATION

**Before (Needs Optimization):**
```
MLmodelsareincrediblyusefultheycanhelpyousolvecomplexproblemsquickly&efficientlybuttheyrequirecarefultuning

optimization&propertrainingdatatoworkwellinthisscriptwellexplorehowtoimproveyourmodelsperformance
```

**After (Optimized for TTS):**
```
Machine learning models are incredibly useful. They can help you solve complex problems quickly and efficiently.

However, these models require careful attention. You need proper tuning, optimization, and quality training data.

In this tutorial, we'll explore practical ways to improve your model's performance. Let's get started.
```

**What Changed:**
- ✅ Added spaces and punctuation
- ✅ Broke into short sentences
- ✅ Split into logical paragraphs
- ✅ Removed special characters
- ✅ Added conversational transitions
- ✅ Clear, natural flow

---

### YOUR SCRIPT ANALYSIS

**Send me your script and I'll:**
1. ✅ Identify optimization opportunities
2. ✅ Suggest specific improvements
3. ✅ Rewrite problem sections
4. ✅ Recommend voice & speed settings
5. ✅ Estimate audio duration
6. ✅ Generate optimized version ready for TTS

**Or choose:**
A) Analyze specific sections you're concerned about
B) Get general optimization tips for your content type
C) See before/after examples for your industry
D) Proceed with optimization and generation

Ready to make your script TTS-perfect! 🚀
"""


def create_troubleshooting_prompt() -> str:
    """Generate TTS troubleshooting guide prompt.

    Returns:
        Formatted troubleshooting guide
    """
    return """🔧 **TTS TROUBLESHOOTING GUIDE**

Having issues with audio quality? Let's diagnose and fix it!

---

### COMMON ISSUES & SOLUTIONS

**1. "VOICE SOUNDS ROBOTIC / UNNATURAL"** 🤖

**Symptoms:**
- Monotone delivery
- Lack of emotion
- Mechanical pacing

**Solutions:**
✅ Enable audio enhancement: `enhance=True`
✅ Adjust speed to 0.95-1.05 (not exactly 1.0)
✅ Break text into shorter segments (100-250 tokens)
✅ Add punctuation for natural pauses
✅ Use a higher-quality voice (af_bella, af_nicole, bf_emma)

**Try this:**
```python
# Instead of:
generate("Long text...", speed=1.0, enhance=False)

# Do this:
generate("Shorter segments.", speed=0.98, enhance=True)
```

---

**2. "WORDS ARE MISPRONOUNCED"** 🗣️

**Common culprits:**
- Acronyms: "AI" might be "ay-eye" or "eh-ee"
- Technical terms: "API", "SQL", "HTTP"
- Brand names: "AWS", "GitHub"
- Numbers: "2024" as "two thousand twenty-four" vs "twenty twenty-four"

**Solutions:**
✅ Spell out acronyms phonetically: "A.I." or "Artificial Intelligence"
✅ Use alternative spelling: "sequel" for "SQL"
✅ Test pronunciation first with short samples
✅ Add pronunciation hints with hyphens: "re-evaluate"

**Example fixes:**
- "API" → "A.P.I." or "Application Programming Interface"
- "SQL" → "sequel" or "S.Q.L."
- "ML" → "machine learning" (spell out on first use)
- "2024" → "twenty twenty-four" (write it out)

---

**3. "PACING IS TOO FAST / TOO SLOW"** ⏩⏪

**Symptoms:**
- Rushed speech (hard to follow)
- Unnaturally slow (boring)
- Inconsistent pace

**Solutions:**
✅ Adjust speed parameter:
  - Too fast? Try 0.90-0.95
  - Too slow? Try 1.05-1.10
  - Find sweet spot: 0.95-1.05 for most content

✅ Check text length:
  - >400 tokens = rushed (chunk it down!)
  - <100 tokens = may sound odd (combine segments)

✅ Use different speeds for different sections:
  - Important info: 0.95x
  - Casual chat: 1.0-1.05x
  - Excitement: 1.1-1.2x

---

**4. "AUDIO HAS CLICKS / POPS / ARTIFACTS"** 🔊

**Symptoms:**
- Clicking sounds between words
- Popping at segment boundaries
- Audio glitches

**Solutions:**
✅ Enable audio enhancement: `enhance=True`
✅ Use crossfade between segments: `crossfade_duration=0.1`
✅ Increase gap duration: `gap_duration=0.5` or higher
✅ Check source text for special characters (remove @, #, etc.)

**For podcast/multi-segment:**
```python
combine_audio_segments(
    segments,
    gap_duration=0.6,       # Longer gap prevents clicks
    crossfade_duration=0.1  # Smooth transitions
)
```

---

**5. "VOLUME IS INCONSISTENT"** 📊

**Symptoms:**
- Some parts loud, some quiet
- Hard to hear certain sections
- Dynamic range issues

**Solutions:**
✅ Always enable enhancement: `enhance=True`
✅ Use consistent voice across project
✅ Check source text punctuation (affects emphasis)
✅ Avoid mixing voices with very different qualities

**Enhancement handles:**
- Normalization (consistent volume)
- Noise reduction
- Fade in/out
- Silence trimming

---

**6. "PAUSES ARE AWKWARD / WRONG"** ⏸️

**Symptoms:**
- Pauses in wrong places
- No pause where needed
- Unnatural rhythm

**Solutions:**
✅ Add punctuation strategically:
  - Period (.) = full stop
  - Comma (,) = brief pause
  - Ellipsis (...) = longer pause
  - Em dash (—) = dramatic pause

✅ Adjust gap duration between segments:
  - Tutorial: 0.5s
  - Podcast: 0.4-0.6s
  - Meditation: 1.0s+
  - Fast-paced: 0.3s

**Example:**
```
Bad: "Welcome to my channel today we'll discuss AI"
Good: "Welcome to my channel. Today, we'll discuss AI."
Even better: "Welcome to my channel... Today, we'll discuss AI."
```

---

**7. "SCRIPT TOO LONG / RUSHED AT END"** 📏

**Symptoms:**
- First part sounds good
- Last part sounds rushed
- Overall quality degrades

**Root cause:** Token limit exceeded (>450 tokens)

**Solutions:**
✅ Auto-chunking is enabled by default (handles this automatically)
✅ Split script into logical paragraphs
✅ Use `process_script()` for long content
✅ Aim for 100-250 tokens per segment

**Check token count:**
```python
# Estimate: ~1 token per 4 characters
text_length = len(your_text)
approx_tokens = text_length / 4

if approx_tokens > 400:
    print("⚠️ Consider splitting into smaller chunks")
```

---

**8. "WRONG VOICE FOR CONTENT"** 🎭

**Symptoms:**
- Voice doesn't match tone
- Sounds unprofessional
- Mismatched expectations

**Solution: Voice Selection Guide**

**For Technical/Tutorial:**
✅ am_michael (authoritative, clear)
✅ af_sarah (professional, crisp)

**For Warm/Engaging:**
✅ af_bella (warmest, most expressive)
✅ af_nicole (versatile, dynamic)

**For British Accent:**
✅ bm_george (distinguished)
✅ bf_emma (professional)

**For Casual/Energetic:**
✅ af_sky (youthful)
✅ am_adam (casual)

**For Long Content (>30 min):**
✅ Use PREMIUM voices only:
   - af_bella (A- grade)
   - af_nicole (B- grade)
   - bf_emma (B- grade)

---

### DIAGNOSTIC WORKFLOW

**Step 1: Identify Issue Category**
- Sound quality (robotic, artifacts)
- Pronunciation (wrong words)
- Pacing (too fast/slow)
- Technical (volume, pauses)

**Step 2: Apply Quick Fixes**
- Enable enhancement
- Adjust speed
- Fix text formatting
- Check voice choice

**Step 3: Test Small Sample**
- Generate 1-2 sentences
- Listen critically
- Iterate on fixes

**Step 4: Apply to Full Script**
- Use working settings
- Process entire content
- Verify quality throughout

---

### PREVENTION CHECKLIST ✅

Before generating, ensure:
- [ ] Enhancement enabled
- [ ] Appropriate voice selected
- [ ] Speed in 0.9-1.1 range
- [ ] Text properly punctuated
- [ ] No special characters (@, #, &)
- [ ] Segments under 400 tokens
- [ ] Acronyms spelled out
- [ ] Numbers written as words (if important)

---

### STILL HAVING ISSUES?

**Tell me:**
1. **What's the specific problem?**
   - Exact symptoms you're hearing
   - Which part of the audio

2. **Your current settings:**
   - Voice being used
   - Speed setting
   - Enhancement on/off

3. **Sample of your text:**
   - Show me the problematic section
   - ~50-100 words

**And I'll provide:**
- ✅ Root cause analysis
- ✅ Specific fix for your case
- ✅ Settings recommendations
- ✅ Optimized text if needed
- ✅ Alternative approaches

**Or select quick help:**
A) Voice isn't right for my content
B) Specific words sound wrong
C) Quality issues (clicks, volume)
D) Pacing problems
E) Something else

Let's get your TTS sounding perfect! 🎯
"""


# Helper function for voice recommendation logic
def get_voice_recommendation(content_type: str, tone: str, rank: int) -> str:
    """Get voice recommendation based on content type and tone.

    Args:
        content_type: Type of content
        tone: Desired tone
        rank: Ranking position (1-3)

    Returns:
        Voice recommendation string
    """
    recommendations = {
        "tutorial": ["am_michael", "af_sarah", "af_bella"],
        "podcast": ["af_bella", "am_michael", "af_nicole"],
        "audiobook": ["af_bella", "bm_george", "af_nicole"],
        "news": ["am_michael", "af_sarah", "bm_george"],
        "meditation": ["bf_isabella", "af_bella"],
        "vlog": ["af_sky", "am_adam", "af_nicole"],
    }

    default = ["af_bella", "am_michael", "af_sarah"]
    voices = recommendations.get(content_type.lower(), default)

    if rank <= len(voices):
        voice_id = voices[rank - 1]
        info = VOICE_CHARACTERISTICS.get(voice_id, {})
        char = info.get("characteristics", ["Versatile voice"])[0]
        return f"`{voice_id}` - {char}"

    return "`af_bella` - Warm and versatile (default)"
