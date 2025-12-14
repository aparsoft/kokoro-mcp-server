import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import sys
import warnings

# Suppress warnings from PyTorch and other libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aparsoft_tts.core.engine_factory import get_tts_engine


# Import error handling utilities
from streamlit_utils import (
    streamlit_error_handler,
    safe_json_serialize,
)

# Import new engine and audio features
from aparsoft_tts.core.engine import (
    ALL_VOICES,
    VOICE_REGISTRY,
    VoiceInfo,
    parse_mixed_voice,
    TTSEngine,
)
from aparsoft_tts.utils.audio import (
    FadeCurve,
    analyze_audio,
    format_duration,
)


# Helper wrapper for get_voice_info
def get_voice_info(voice_id: str) -> VoiceInfo | None:
    """Get voice info from registry."""
    return VOICE_REGISTRY.get(voice_id)


# ==========================================
# VOICE HELPER FUNCTIONS (NEW)
# ==========================================


def get_voice_display_name(voice_id: str) -> str:
    """Get a display-friendly voice name with metadata.

    Args:
        voice_id: The voice identifier (e.g., 'af_sarah')

    Returns:
        Formatted display name like 'af_sarah - American Female - warm, expressive'
    """
    info = get_voice_info(voice_id)
    if info:
        return f"{voice_id} - {info.accent} {info.gender.title()} - {info.description[:30]}"
    return voice_id


def get_voices_by_category() -> Dict[str, List[str]]:
    """Get voices organized by category.

    Returns:
        Dict mapping category names to voice lists
    """
    categories = {
        "👨 American Male": [],
        "👩 American Female": [],
        "🎩 British Male": [],
        "👒 British Female": [],
        "🇮🇳 Hindi Voices": [],
        "✨ Special": [],
    }

    for voice_id, info in VOICE_REGISTRY.items():
        if info.accent == "Hindi":
            categories["🇮🇳 Hindi Voices"].append(voice_id)
        elif info.gender == "male" and info.accent == "American":
            categories["👨 American Male"].append(voice_id)
        elif info.gender == "female" and info.accent == "American":
            categories["👩 American Female"].append(voice_id)
        elif info.gender == "male" and info.accent == "British":
            categories["🎩 British Male"].append(voice_id)
        elif info.gender == "female" and info.accent == "British":
            categories["👒 British Female"].append(voice_id)
        else:
            categories["✨ Special"].append(voice_id)

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def validate_voice_mix(voice_spec: str) -> tuple[bool, str]:
    """Validate a voice mixing specification.

    Args:
        voice_spec: Voice spec like 'af_sky+af_bella' or 'af_sky*0.7+af_bella*0.3'

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        voices = parse_mixed_voice(voice_spec)
        if not voices:
            return False, "No valid voices found"
        return True, f"✅ Valid mix: {len(voices)} voices"
    except Exception as e:
        return False, f"❌ Invalid: {str(e)}"


# ==========================================
# AUDIO HELPER FUNCTIONS (NEW)
# ==========================================


def get_audio_stats(audio_path: str | Path) -> Dict[str, Any]:
    """Get comprehensive audio statistics for display.

    Args:
        audio_path: Path to audio file

    Returns:
        Dict with formatted audio statistics
    """
    try:
        import soundfile as sf

        audio, sr = sf.read(str(audio_path))
        stats = analyze_audio(audio, sr)

        return {
            "duration": format_duration(stats["duration_seconds"]),
            "duration_seconds": stats["duration_seconds"],
            "sample_rate": f"{sr:,} Hz",
            "samples": f"{stats['samples']:,}",
            "peak_db": f"{stats['peak_db']:.1f} dB",
            "rms_db": f"{stats['rms_db']:.1f} dB",
            "channels": 1,  # mono assumed for TTS
        }
    except Exception as e:
        return {"error": str(e)}


def get_fade_curve_options() -> Dict[str, FadeCurve]:
    """Get fade curve options for UI selection.

    Returns:
        Dict mapping display names to FadeCurve enum values
    """
    return {
        "Cosine (Smoothest)": FadeCurve.COSINE,
        "Linear (Simple)": FadeCurve.LINEAR,
        "Exponential (Punchy)": FadeCurve.EXPONENTIAL,
        "Logarithmic (Natural)": FadeCurve.LOGARITHMIC,
    }


# ==========================================
# ENGINE HELPER FUNCTIONS
# ==========================================


@streamlit_error_handler()
def get_current_engine():
    """Get or initialize the current TTS engine using factory pattern."""
    engine_type = st.session_state.current_engine_type

    # Check if engine is already cached
    if engine_type not in st.session_state.engine_cache:
        with st.spinner(f"🔄 Loading {engine_type} engine..."):
            engine = get_tts_engine(engine_type)
            st.session_state.engine_cache[engine_type] = engine

    return st.session_state.engine_cache[engine_type]


def get_engine_capabilities() -> Dict[str, Any]:
    """Get current engine capabilities for UI adaptation.

    Returns:
        Dict with engine capabilities
    """
    engine_type = st.session_state.current_engine_type

    capabilities = {
        "kokoro": {
            "supports_voice_mixing": True,
            "supports_timestamps": True,
            "supports_streaming": True,
            "supports_concurrent": True,
            "max_voices": 15,
        },
        "indic": {
            "supports_voice_mixing": False,
            "supports_timestamps": False,
            "supports_streaming": False,
            "supports_concurrent": True,
            "max_voices": 4,
        },
        "openvoice": {
            "supports_voice_mixing": False,
            "supports_timestamps": False,
            "supports_streaming": False,
            "supports_concurrent": False,
            "max_voices": 1,  # Custom cloning
        },
    }

    return capabilities.get(engine_type, capabilities["kokoro"])


# ==========================================
# HISTORY HELPER FUNCTIONS
# ==========================================


def add_to_history(entry: Dict[str, Any]):
    """Add generation to history with enhanced metadata."""
    entry["timestamp"] = datetime.now().isoformat()
    entry["engine"] = st.session_state.current_engine_type

    # Add audio stats if output path exists
    if "output_path" in entry:
        stats = get_audio_stats(entry["output_path"])
        if "error" not in stats:
            entry["audio_stats"] = stats

    st.session_state.generation_history.append(entry)
    st.session_state.total_generations += 1

    # Update total duration
    if "duration" in entry:
        st.session_state.total_duration += entry.get("duration", 0)


def get_history_df() -> pd.DataFrame:
    """Convert history to pandas DataFrame with enhanced columns."""
    if not st.session_state.generation_history:
        return pd.DataFrame()

    df = pd.DataFrame(st.session_state.generation_history)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Add engine column if not present
    if "engine" not in df.columns:
        df["engine"] = "kokoro"  # Default for legacy entries

    return df


def get_history_summary() -> Dict[str, Any]:
    """Get summary statistics from history.

    Returns:
        Dict with summary statistics
    """
    df = get_history_df()
    if df.empty:
        return {
            "total_generations": 0,
            "total_duration": "00:00.000",
            "avg_generation_time": 0,
            "unique_voices": 0,
            "most_used_voice": None,
        }

    total_duration = df["duration"].sum() if "duration" in df.columns else 0

    return {
        "total_generations": len(df),
        "total_duration": format_duration(total_duration),
        "avg_generation_time": (
            df["generation_time"].mean() if "generation_time" in df.columns else 0
        ),
        "unique_voices": df["voice"].nunique() if "voice" in df.columns else 0,
        "most_used_voice": (
            df["voice"].mode().iloc[0]
            if "voice" in df.columns and not df["voice"].mode().empty
            else None
        ),
    }


@streamlit_error_handler(show_traceback=False, log_to_file=True)
def save_history():
    """Save history to JSON file"""
    history_file = Path("data/generation_history.json")
    history_file.parent.mkdir(parents=True, exist_ok=True)

    with open(history_file, "w") as f:
        # Use safe serialization to handle any Path objects
        safe_data = safe_json_serialize(st.session_state.generation_history)
        json.dump(safe_data, f, indent=2)


@streamlit_error_handler(show_traceback=False, log_to_file=True)
def load_history():
    """Load history from JSON file"""
    history_file = Path("data/generation_history.json")

    if history_file.exists():
        with open(history_file, "r") as f:
            st.session_state.generation_history = json.load(f)
            st.session_state.total_generations = len(st.session_state.generation_history)


# Load history on startup
load_history()
