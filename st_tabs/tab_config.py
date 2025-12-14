import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
import numpy as np
import soundfile as sf
from typing import List, Dict, Any
import sys
import os
import warnings

# Suppress warnings from PyTorch and other libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aparsoft_tts.core.engine_factory import get_tts_engine, get_engine_info, compare_engines
from aparsoft_tts.core.engine import (
    ALL_VOICES,
    MALE_VOICES,
    FEMALE_VOICES,
    HINDI_MALE_VOICES,
    HINDI_FEMALE_VOICES,
)
from aparsoft_tts import TTSConfig
from aparsoft_tts.utils.audio import enhance_audio, FadeCurve
from aparsoft_tts.config import get_config

# Import error handling utilities
from streamlit_utils import (
    streamlit_error_handler,
    show_exception,
    safe_json_serialize,
    extract_voices_from_history,
    normalize_voice_column,
)

from st_utils.helper import (
    get_current_engine,
    add_to_history,
    get_voice_display_name,
    get_fade_curve_options,
)


# ==========================================
# TAB 8: CONFIGURATION (ENHANCED)
# ==========================================
def render_tab_config():
    """Render the Configuration tab with enhanced audio settings"""
    st.markdown("## ⚙️ Configuration")
    st.markdown("Manage TTS engine and advanced audio processing settings")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎤 TTS Settings")

        config_voice = st.selectbox(
            "Default Voice",
            options=ALL_VOICES,
            index=ALL_VOICES.index("am_michael"),
            format_func=get_voice_display_name,
            key="config_voice",
        )

        config_speed = st.slider(
            "Default Speed", min_value=0.5, max_value=2.0, value=1.0, step=0.1, key="config_speed"
        )

        config_enhance = st.checkbox(
            "Enable Audio Enhancement by Default", value=True, key="config_enhance"
        )

        config_sample_rate = st.selectbox(
            "Sample Rate",
            options=[16000, 22050, 24000, 44100, 48000],
            index=2,
            key="config_sample_rate",
        )

        config_output_format = st.selectbox(
            "Output Format", options=["wav", "flac", "mp3"], index=0, key="config_format"
        )

    with col2:
        st.markdown("### 🔊 Audio Processing")

        config_trim = st.checkbox("Trim Silence", value=True, key="config_trim")

        if config_trim:
            config_trim_db = st.slider(
                "Trim Threshold (dB)",
                min_value=10.0,
                max_value=60.0,
                value=25.0,  # Updated default for better initial consonant preservation
                step=5.0,
                key="config_trim_db",
                help="Lower = more conservative (preserves more audio). Recommended: 20-30 dB",
            )
        else:
            config_trim_db = 25.0

        # Fade curve selection (new!)
        fade_options = get_fade_curve_options()
        config_fade_curve = st.selectbox(
            "Fade Curve Type",
            options=list(fade_options.keys()),
            index=0,
            key="config_fade_curve",
            help="Shape of fade in/out transitions",
        )

        config_fade = st.slider(
            "Fade Out Duration (seconds)",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.05,
            key="config_fade",
            help="Fade-in is always short (15-20ms) to preserve initial consonants",
        )

        config_chunk_gap = st.slider(
            "Chunk Gap Duration (seconds)",
            min_value=0.0,
            max_value=2.0,
            value=0.2,
            step=0.1,
            key="config_chunk_gap",
        )

    # Advanced Audio Enhancement
    st.markdown("---")
    st.markdown("### 🎹 Advanced Audio Enhancement")

    col1, col2 = st.columns(2)

    with col1:
        config_normalize = st.checkbox(
            "Normalize Audio",
            value=True,
            key="config_normalize",
            help="Normalize volume levels with professional headroom",
        )

        if config_normalize:
            config_headroom = st.slider(
                "Headroom (dB)",
                min_value=-6.0,
                max_value=0.0,
                value=-1.0,
                step=0.5,
                key="config_headroom",
                help="Headroom below 0dBFS. -1.0 dB is industry standard",
            )
        else:
            config_headroom = -1.0

        config_noise_reduction = st.checkbox(
            "Noise Reduction",
            value=True,
            key="config_noise_reduction",
            help="Apply spectral noise reduction (noisereduce v3.0)",
        )

    with col2:
        config_crossfade = st.slider(
            "Crossfade Duration (seconds)",
            min_value=0.0,
            max_value=0.5,
            value=0.1,
            step=0.05,
            key="config_crossfade",
            help="Smooth transitions between segments",
        )

        # Voice-specific settings info
        st.info(
            """
        **🎯 Initial Consonant Protection:**
        - Margin: 120ms (protects "All", "The", etc.)
        - Fade-in: 15ms (anti-click only)
        - Padding: 100ms (safety buffer)
        """
        )

    if st.button("💾 Save Configuration", type="primary", width="stretch"):
        try:
            # Create custom config with all settings
            custom_config = TTSConfig(
                voice=config_voice,
                speed=config_speed,
                enhance_audio=config_enhance,
                sample_rate=config_sample_rate,
                output_format=config_output_format,
                trim_silence=config_trim,
                trim_db=config_trim_db if config_trim else 25.0,
                fade_duration=config_fade,
                chunk_gap_duration=config_chunk_gap,
                podcast_crossfade_duration=config_crossfade,
            )

            # Save to file
            config_dir = Path("config")
            config_dir.mkdir(parents=True, exist_ok=True)

            config_file = config_dir / "custom_config.json"

            # ✅ FIX: Use model_dump_json() to handle Path serialization
            with open(config_file, "w") as f:
                f.write(custom_config.model_dump_json(indent=2))

            # Clear engine cache to force reload with new config
            st.session_state.engine_cache.clear()

            st.success("✅ Configuration saved! Engines will reload with new settings on next use.")

        except Exception as e:
            # Show detailed error with full traceback
            st.error(f"❌ Failed to save configuration: {str(e)}")

            # Show full traceback in expandable section
            with st.expander("🔍 Full Error Details"):
                import traceback

                st.code(traceback.format_exc(), language="python")

    # Current Configuration Display
    st.markdown("---")
    st.markdown("### 📋 Current Configuration")

    try:
        engine = get_current_engine()
        config = engine.config

        config_data = {
            "Voice": config.voice,
            "Speed": config.speed,
            "Sample Rate": f"{config.sample_rate} Hz",
            "Output Format": config.output_format.upper(),
            "Enhancement": "Enabled" if config.enhance_audio else "Disabled",
            "Trim Silence": "Enabled" if config.trim_silence else "Disabled",
            "Trim Threshold": f"{config.trim_db} dB",
            "Fade Duration": f"{config.fade_duration}s",
            "Chunk Gap": f"{config.chunk_gap_duration}s",
        }

        # Convert all values to strings to avoid Arrow serialization issues
        config_items = [(k, str(v)) for k, v in config_data.items()]
        config_df = pd.DataFrame(config_items, columns=["Setting", "Value"])
        st.dataframe(config_df, width="stretch", hide_index=True)
    except Exception as e:
        st.info("💡 Load an engine first to view its configuration")
