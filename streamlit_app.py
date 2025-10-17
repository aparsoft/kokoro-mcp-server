# streamlit_app.py

"""
Aparsoft TTS - Enterprise-Grade Streamlit Management Interface

A comprehensive web UI for managing all Aparsoft TTS functionality:
- Single & Batch Speech Generation
- Script Processing
- Voice Comparison
- Audio Enhancement
- Configuration Management
- MCP Server Status
- Analytics & History
"""

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
sys.path.insert(0, str(Path(__file__).parent))

from aparsoft_tts.core.engine_factory import get_tts_engine, get_engine_info, compare_engines
from aparsoft_tts.core.engine import (
    ALL_VOICES,
    MALE_VOICES,
    FEMALE_VOICES,
    HINDI_MALE_VOICES,
    HINDI_FEMALE_VOICES,
)
from aparsoft_tts import TTSConfig
from aparsoft_tts.utils.audio import enhance_audio, get_audio_duration
from aparsoft_tts.config import get_config

# Import error handling utilities
from streamlit_utils import (
    streamlit_error_handler,
    show_exception,
    safe_json_serialize,
    extract_voices_from_history,
    normalize_voice_column,
)

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Aparsoft TTS Manager",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# CUSTOM CSS
# ==========================================
st.markdown(
    """
<style>
    /* Main container */
    .main {
        padding: 2rem;
    }
    
    /* Header styling */
    .big-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    /* Card styling */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .metric-card h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    
    .metric-card p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Voice card */
    .voice-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .voice-card h4 {
        margin: 0 0 0.5rem 0;
        color: #667eea;
    }
    
    /* Success/Error messages */
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        color: #155724;
        margin: 1rem 0;
    }
    
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        color: #721c24;
        margin: 1rem 0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "engine_cache" not in st.session_state:
    st.session_state.engine_cache = {}

if "current_engine_type" not in st.session_state:
    st.session_state.current_engine_type = "kokoro"

if "generation_history" not in st.session_state:
    st.session_state.generation_history = []

if "total_generations" not in st.session_state:
    st.session_state.total_generations = 0

if "total_duration" not in st.session_state:
    st.session_state.total_duration = 0.0

if "podcast_segments" not in st.session_state:
    st.session_state.podcast_segments = []

if "podcast_segment_counter" not in st.session_state:
    st.session_state.podcast_segment_counter = 0

# ==========================================
# HELPER FUNCTIONS
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


def add_to_history(entry: Dict[str, Any]):
    """Add generation to history"""
    entry["timestamp"] = datetime.now().isoformat()
    st.session_state.generation_history.append(entry)
    st.session_state.total_generations += 1


def get_history_df() -> pd.DataFrame:
    """Convert history to pandas DataFrame"""
    if not st.session_state.generation_history:
        return pd.DataFrame()

    df = pd.DataFrame(st.session_state.generation_history)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


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

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("### 🎙️ Aparsoft TTS")
    st.markdown("---")

    # Quick Stats
    st.markdown("### 📊 Quick Stats")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Generations", st.session_state.total_generations)
    with col2:
        current_engine_type = st.session_state.current_engine_type
        is_loaded = current_engine_type in st.session_state.engine_cache
        st.metric("Engine Loaded", "Yes" if is_loaded else "No")

    st.markdown("---")

    # Engine Selection
    st.markdown("### 🎨 Engine Selection")

    engine_options = {
        "kokoro": "🚀 Kokoro (Fast English)",
        "indic": "🇮🇳 Indic Parler-TTS (Hindi)",
        "openvoice": "🎭 OpenVoice (Cloning)",
    }

    selected_engine = st.selectbox(
        "Choose TTS Engine",
        options=list(engine_options.keys()),
        format_func=lambda x: engine_options[x],
        index=list(engine_options.keys()).index(st.session_state.current_engine_type),
        help="Select the TTS engine to use",
    )

    # Update session state if engine changed
    if selected_engine != st.session_state.current_engine_type:
        st.session_state.current_engine_type = selected_engine
        st.rerun()

    # Show engine info
    try:
        engine_info = get_engine_info(selected_engine)
        with st.expander("ℹ️ Engine Details", expanded=False):
            st.markdown(f"**Model:** {engine_info['model_size']}")
            st.markdown(f"**Languages:** {', '.join(engine_info['languages'])}")
            st.markdown(f"**Voices:** {engine_info['voice_count']}")
            st.markdown(f"**Speed:** {engine_info['speed']}")
    except Exception as e:
        st.warning(f"Could not load engine info: {str(e)}")

    st.markdown("---")

    # Engine Status
    st.markdown("### ⚙️ Engine Status")

    current_engine_type = st.session_state.current_engine_type
    is_loaded = current_engine_type in st.session_state.engine_cache

    if is_loaded:
        st.success(f"✅ {current_engine_type.upper()} Engine Ready")
        if st.button("🔄 Reload Engine", width="stretch"):
            # Clear current engine from cache to force reload
            if current_engine_type in st.session_state.engine_cache:
                del st.session_state.engine_cache[current_engine_type]
            st.rerun()
    else:
        st.info(f"⏳ {current_engine_type.upper()} Engine Not Loaded")
        if st.button("🚀 Load Engine", width="stretch"):
            get_current_engine()  # This will load and cache the engine
            st.rerun()

    st.markdown("---")

    # Presets Manager
    st.markdown("### 💾 Presets")

    # Load presets from file
    presets_file = Path("config/presets.json")

    def load_presets():
        if presets_file.exists():
            with open(presets_file, "r") as f:
                return json.load(f)
        return {}

    def save_presets(presets):
        presets_file.parent.mkdir(parents=True, exist_ok=True)
        with open(presets_file, "w") as f:
            json.dump(presets, f, indent=2)

    presets = load_presets()

    if presets:
        selected_preset = st.selectbox(
            "Load Preset",
            options=list(presets.keys()),
            key="preset_select",
        )

        if st.button("📥 Load", width="stretch"):
            preset = presets[selected_preset]
            st.success(f"✅ Loaded preset: {selected_preset}")
            st.info(f"Voice: {preset.get('voice', 'N/A')} | Speed: {preset.get('speed', 'N/A')}")
    else:
        st.info("📝 No presets saved yet")

    # Save current engine config as preset
    preset_name = st.text_input(
        "Preset Name", placeholder="My Podcast Setup", key="new_preset_name"
    )

    if st.button("💾 Save Current Config", width="stretch"):
        if preset_name:
            if st.session_state.engine:
                config = st.session_state.engine.config
                presets[preset_name] = {
                    "voice": config.voice,
                    "speed": config.speed,
                    "enhance_audio": config.enhance_audio,
                    "sample_rate": config.sample_rate,
                    "output_format": config.output_format,
                    "trim_db": config.trim_db,
                }
                save_presets(presets)
                st.success(f"✅ Saved preset: {preset_name}")
                st.rerun()
            else:
                st.error("❌ Engine not initialized")
        else:
            st.error("❌ Please enter a preset name")

    st.markdown("---")

    # Quick Actions
    st.markdown("### ⚡ Quick Actions")

    if st.button("📥 Export History", width="stretch"):
        save_history()
        st.success("✅ History exported!")

    if st.button("🗑️ Clear History", width="stretch"):
        st.session_state.generation_history = []
        st.session_state.total_generations = 0
        st.rerun()

    st.markdown("---")

    # About
    st.markdown("### ℹ️ About")
    st.markdown(
        """
    **Aparsoft TTS Manager**
    
    Enterprise-grade Text-to-Speech management interface powered by Kokoro-82M.
    
    - 🎤 12 Professional Voices
    - 🔊 Audio Enhancement
    - 📦 Batch Processing
    - 📊 Analytics Dashboard
    
    **Contact:**
    - 📧 contact@aparsoft.com
    - 🌐 aparsoft.com
    """
    )

# ==========================================
# MAIN CONTENT
# ==========================================

# Header
st.markdown("<h1 class='big-title'>🎙️ Aparsoft TTS Manager</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='subtitle'>Enterprise Text-to-Speech Management Console</p>", unsafe_allow_html=True
)

# OpenVoice Studio Link
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 1.5rem;
                    border-radius: 12px;
                    text-align: center;
                    box-shadow: 0 4px 12px rgba(240, 147, 251, 0.3);'>
            <h3 style='color: white; margin: 0 0 0.5rem 0; font-size: 1.5rem;'>🎙️ OpenVoice V2 Studio</h3>
            <p style='color: rgba(255,255,255,0.9); margin: 0 0 1rem 0;'>
                Zero-shot voice cloning with cross-lingual generation
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Check if OpenVoice is available
    try:
        from aparsoft_tts.core.openvoice_engine import OpenVoiceEngine

        openvoice_available = True
    except:
        openvoice_available = False

    if openvoice_available:
        # Navigate to OpenVoice Studio page
        if st.button(
            "🚀 Launch OpenVoice Studio",
            type="primary",
            use_container_width=True,
            help="Clone ANY voice from 3-5s audio | 6 languages | Cross-lingual generation",
        ):
            st.info(
                """ 
            👉 **OpenVoice Studio is now available as a separate page!**
            
            Navigate using the sidebar or visit the page directly:
            - Look for **"🎙️ OpenVoice Studio"** in the sidebar navigation
            - Or use the Streamlit navigation menu
            """
            )
    else:
        st.warning(
            """
        ⚠️ **OpenVoice V2 not installed**
        
        To enable voice cloning:
        1. `pip install -e ".[openvoice]"`
        2. `pip install git+https://github.com/myshell-ai/MeloTTS.git`
        3. `python -m aparsoft_tts.download_openvoice_checkpoints`
        
        See README_OPENVOICE.md for details.
        """
        )

st.markdown("---")

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(
    [
        "🎯 Single",
        "📦 Batch",
        "📄 Script",
        "🎙️ Podcast",
        "🎤 Transcribe",
        "🔍 Voices",
        "📁 Files",
        "⚙️ Config",
        "📊 Analytics",
    ]
)

# ==========================================
# TAB 1: SINGLE GENERATION
# ==========================================
with tab1:
    st.markdown("## 🎯 Single Speech Generation")
    st.markdown("Generate high-quality speech from text with customizable parameters")

    col1, col2 = st.columns([2, 1])

    with col1:
        text_input = st.text_area(
            "Enter text to convert to speech",
            height=150,
            placeholder="Type or paste your text here...",
            help="Maximum 10,000 characters",
        )

    with col2:
        st.markdown("### Settings")

        # Get appropriate voice list based on selected engine
        current_engine = st.session_state.current_engine_type
        if current_engine == "indic":
            # For Indic engine, show Hindi voices
            from aparsoft_tts.core.engine_indic_parler import (
                HINDI_VOICES,
                ALL_INDIC_VOICES,
                EMOTIONS,
            )

            voice_options = ALL_INDIC_VOICES
            default_voice = "rohit"
        elif current_engine == "openvoice":
            # OpenVoice uses reference audio, but we can show base speakers
            voice_options = ["default"]
            default_voice = "default"
        else:  # kokoro
            voice_options = ALL_VOICES
            default_voice = "am_michael"

        voice = st.selectbox(
            "Voice",
            options=voice_options,
            index=voice_options.index(default_voice) if default_voice in voice_options else 0,
            help=f"Select the voice for generation ({current_engine} engine)",
        )

        # Emotion selector for Indic engine
        emotion = None
        if current_engine == "indic":
            emotion = st.selectbox(
                "Emotion", options=EMOTIONS, index=0, help="Emotion/style for the generated speech"
            )

        speed = st.slider(
            "Speed",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Speech speed multiplier",
        )

        enhance = st.checkbox(
            "Enable Audio Enhancement",
            value=True,
            help="Apply normalization, noise reduction, and fades",
        )

        output_format = st.selectbox(
            "Output Format",
            options=["wav", "flac", "mp3"],
            index=0,
            help="WAV: Uncompressed | FLAC: Lossless | MP3: Compressed",
        )

        output_name = st.text_input(
            "Output filename",
            value=f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{output_format}",
            help="Name for the output file",
        )

    # Token Analysis & Quality Check
    if text_input:
        with st.expander("📊 Token Analysis & Quality Check"):
            try:
                engine = get_current_engine()
                if engine:
                    token_count = engine._count_tokens(text_input)
                    chunks = engine._chunk_text_smart(text_input)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Tokens", token_count)
                    with col2:
                        st.metric("Chunks", len(chunks))
                    with col3:
                        if token_count <= 250:
                            st.metric("Status", "✅ Optimal")
                        else:
                            st.metric("Status", "⚠️ Will Chunk")

                    # Quality warnings
                    warnings = []
                    if token_count > 400:
                        warnings.append("⚠️ Text is long - will be chunked (may affect pacing)")
                    if speed > 1.5:
                        warnings.append("⚠️ High speed may reduce quality")
                    if len(text_input) < 10:
                        warnings.append("⚠️ Text is very short")

                    if warnings:
                        st.warning("Quality Warnings:")
                        for warning in warnings:
                            st.write(warning)

                    # Show chunk breakdown
                    if len(chunks) > 1:
                        st.markdown("**Chunk Breakdown:**")
                        for i, chunk in enumerate(chunks, 1):
                            chunk_tokens = engine._count_tokens(chunk)
                            with st.container():
                                st.text(f"Chunk {i} ({chunk_tokens} tokens): {chunk[:80]}...")
            except:
                pass

    if st.button("🎤 Generate Speech", type="primary", width="stretch"):
        if not text_input:
            st.error("❌ Please enter some text to convert")
        else:
            try:
                engine = get_current_engine()

                if engine:
                    output_dir = Path("outputs/single")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / output_name

                    with st.spinner("🔊 Generating speech..."):
                        start_time = time.time()

                        # Generate with selected format
                        temp_config = engine.config
                        temp_config.output_format = output_format

                        # Prepare generation parameters
                        gen_params = {
                            "text": text_input,
                            "output_path": str(output_path),
                            "voice": voice,
                            "speed": speed,
                            "enhance": enhance,
                        }

                        # Add emotion parameter for Indic engine
                        if current_engine == "indic" and emotion:
                            gen_params["emotion"] = emotion

                        result_path = engine.generate(**gen_params)

                        generation_time = time.time() - start_time

                    # Get audio info
                    audio, sr = sf.read(str(result_path))
                    duration = len(audio) / sr
                    file_size = result_path.stat().st_size

                    # Add to history
                    history_entry = {
                        "type": "single",
                        "engine": current_engine,
                        "text_length": len(text_input),
                        "voice": voice,
                        "speed": speed,
                        "enhance": enhance,
                        "duration": duration,
                        "file_size": file_size,
                        "generation_time": generation_time,
                        "output_path": str(result_path),
                    }

                    # Add emotion for Indic engine
                    if current_engine == "indic" and emotion:
                        history_entry["emotion"] = emotion

                    add_to_history(history_entry)

                    # Success message
                    st.success("✅ Speech generated successfully!")

                    # Display results
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Duration", f"{duration:.2f}s")
                    with col2:
                        st.metric("File Size", f"{file_size/1024:.1f} KB")
                    with col3:
                        st.metric("Generation Time", f"{generation_time:.2f}s")
                    with col4:
                        st.metric("Speed", f"{speed}x")

                    # Audio player
                    st.audio(str(result_path), format="audio/wav")

                    # Download button
                    with open(result_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Audio",
                            data=f,
                            file_name=output_name,
                            mime="audio/wav",
                            width="stretch",
                        )

            except Exception as e:
                show_exception(e, "Speech generation failed")

# ==========================================
# TAB 2: BATCH PROCESSING
# ==========================================
with tab2:
    st.markdown("## 📦 Batch Processing")
    st.markdown("Generate multiple audio files from a list of texts")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Input Texts")

        input_method = st.radio(
            "Input Method", options=["Manual Entry", "File Upload"], horizontal=True
        )

        texts = []

        if input_method == "Manual Entry":
            num_texts = st.number_input("Number of texts", min_value=1, max_value=100, value=3)

            for i in range(num_texts):
                text = st.text_input(f"Text {i+1}", key=f"batch_text_{i}")
                if text:
                    texts.append(text)

        else:
            uploaded_file = st.file_uploader("Upload text file (one text per line)", type=["txt"])

            if uploaded_file:
                content = uploaded_file.read().decode("utf-8")
                texts = [line.strip() for line in content.split("\n") if line.strip()]

                st.info(f"📄 Loaded {len(texts)} texts from file")

                with st.expander("Preview texts"):
                    for i, text in enumerate(texts[:10], 1):
                        st.text(f"{i}. {text[:100]}...")

    with col2:
        st.markdown("### Settings")

        # Get appropriate voice list based on selected engine
        current_engine = st.session_state.current_engine_type
        if current_engine == "indic":
            from aparsoft_tts.core.engine_indic_parler import (
                HINDI_VOICES,
                ALL_INDIC_VOICES,
                EMOTIONS,
            )

            batch_voice_options = ALL_INDIC_VOICES
            batch_default_voice = "rohit"
        elif current_engine == "openvoice":
            batch_voice_options = ["default"]
            batch_default_voice = "default"
        else:  # kokoro
            batch_voice_options = ALL_VOICES
            batch_default_voice = "am_michael"

        batch_voice = st.selectbox(
            "Voice",
            options=batch_voice_options,
            index=(
                batch_voice_options.index(batch_default_voice)
                if batch_default_voice in batch_voice_options
                else 0
            ),
            key="batch_voice",
        )

        # Emotion selector for Indic engine
        batch_emotion = None
        if current_engine == "indic":
            batch_emotion = st.selectbox(
                "Emotion",
                options=EMOTIONS,
                index=0,
                key="batch_emotion",
                help="Emotion/style for the generated speech",
            )

        batch_speed = st.slider(
            "Speed", min_value=0.5, max_value=2.0, value=1.0, step=0.1, key="batch_speed"
        )

        filename_prefix = st.text_input(
            "Filename Prefix", value="batch_audio", help="Prefix for output files"
        )

    if st.button("🎬 Generate Batch", type="primary", width="stretch"):
        if not texts:
            st.error("❌ No texts to process")
        else:
            try:
                engine = get_current_engine()

                if engine:
                    output_dir = Path("outputs/batch") / datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_dir.mkdir(parents=True, exist_ok=True)

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    generated_files = []
                    total_duration = 0.0

                    start_time = time.time()

                    for i, text in enumerate(texts):
                        status_text.text(f"🔊 Generating {i+1}/{len(texts)}: {text[:50]}...")

                        output_file = output_dir / f"{filename_prefix}_{i+1:03d}.wav"

                        # Prepare generation parameters
                        gen_params = {
                            "text": text,
                            "output_path": str(output_file),
                            "voice": batch_voice,
                            "speed": batch_speed,
                            "enhance": True,
                        }

                        # Add emotion parameter for Indic engine
                        if current_engine == "indic" and batch_emotion:
                            gen_params["emotion"] = batch_emotion

                        engine.generate(**gen_params)

                        # Get duration
                        audio, sr = sf.read(str(output_file))
                        duration = len(audio) / sr
                        total_duration += duration

                        generated_files.append(
                            {
                                "file": output_file.name,
                                "text": text[:50] + "..." if len(text) > 50 else text,
                                "duration": f"{duration:.2f}s",
                                "size": f"{output_file.stat().st_size/1024:.1f} KB",
                            }
                        )

                        progress_bar.progress((i + 1) / len(texts))

                    generation_time = time.time() - start_time

                    # Success message
                    st.success(f"✅ Generated {len(texts)} audio files!")

                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Files Generated", len(texts))
                    with col2:
                        st.metric("Total Duration", f"{total_duration:.1f}s")
                    with col3:
                        st.metric("Generation Time", f"{generation_time:.1f}s")
                    with col4:
                        st.metric("Output Dir", output_dir.name)

                    # File list
                    st.markdown("### Generated Files")
                    df = pd.DataFrame(generated_files)
                    st.dataframe(df, width="stretch")

                    # Add to history
                    add_to_history(
                        {
                            "type": "batch",
                            "num_files": len(texts),
                            "voice": batch_voice,
                            "speed": batch_speed,
                            "total_duration": total_duration,
                            "generation_time": generation_time,
                            "output_dir": str(output_dir),
                        }
                    )

            except Exception as e:
                show_exception(e, "Batch generation failed")

# ==========================================
# TAB 3: SCRIPT PROCESSING
# ==========================================
with tab3:
    st.markdown("## 📄 Script Processing")
    st.markdown("Convert complete video scripts to voiceovers with automatic text chunking")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Script Input")

        script_input_method = st.radio(
            "Input Method",
            options=["Direct Text", "Upload File"],
            horizontal=True,
            key="script_input_method",
        )

        script_text = ""

        if script_input_method == "Direct Text":
            script_text = st.text_area(
                "Enter script",
                height=300,
                placeholder="Paste your video script here...",
                help="Script will be automatically chunked for optimal quality",
            )

        else:
            script_file = st.file_uploader("Upload script file", type=["txt", "md"])

            if script_file:
                script_text = script_file.read().decode("utf-8")

                st.info(f"📄 Script loaded ({len(script_text)} characters)")

                with st.expander("Preview script"):
                    st.text(script_text[:500] + "..." if len(script_text) > 500 else script_text)

    with col2:
        st.markdown("### Settings")

        # Get appropriate voice list based on selected engine
        current_engine = st.session_state.current_engine_type
        if current_engine == "indic":
            from aparsoft_tts.core.engine_indic_parler import (
                HINDI_VOICES,
                ALL_INDIC_VOICES,
                EMOTIONS,
            )

            script_voice_options = ALL_INDIC_VOICES
            script_default_voice = "rohit"
        elif current_engine == "openvoice":
            script_voice_options = ["default"]
            script_default_voice = "default"
        else:  # kokoro
            script_voice_options = ALL_VOICES
            script_default_voice = "am_michael"

        script_voice = st.selectbox(
            "Voice",
            options=script_voice_options,
            index=(
                script_voice_options.index(script_default_voice)
                if script_default_voice in script_voice_options
                else 0
            ),
            key="script_voice",
        )

        # Emotion selector for Indic engine
        script_emotion = None
        if current_engine == "indic":
            script_emotion = st.selectbox(
                "Emotion",
                options=EMOTIONS,
                index=0,
                key="script_emotion",
                help="Emotion/style for the generated speech",
            )

        script_speed = st.slider(
            "Speed", min_value=0.5, max_value=2.0, value=1.0, step=0.1, key="script_speed"
        )

        gap_duration = st.slider(
            "Gap Between Segments",
            min_value=0.0,
            max_value=2.0,
            value=0.5,
            step=0.1,
            help="Pause duration between script paragraphs",
        )

        script_output_format = st.selectbox(
            "Output Format",
            options=["wav", "flac", "mp3"],
            index=0,
            help="WAV: Uncompressed | FLAC: Lossless | MP3: Compressed",
            key="script_format",
        )

        script_output_name = st.text_input(
            "Output filename",
            value=f"voiceover_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{script_output_format}",
            key="script_output",
        )

    # Token Analysis for Script
    if script_text:
        with st.expander("📊 Script Token Analysis"):
            try:
                engine = get_current_engine()
                if engine:
                    token_count = engine._count_tokens(script_text)
                    chunks = engine._chunk_text_smart(script_text)

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Tokens", token_count)
                    with col2:
                        st.metric("Chunks", len(chunks))
                    with col3:
                        avg_tokens = token_count // len(chunks) if chunks else 0
                        st.metric("Avg Tokens/Chunk", avg_tokens)
                    with col4:
                        est_duration = token_count * 0.06  # Rough estimate: ~0.06s per token
                        st.metric("Est. Duration", f"{est_duration:.0f}s")

                    # Show chunk breakdown
                    if len(chunks) > 1:
                        with st.expander(f"View {len(chunks)} chunks"):
                            for i, chunk in enumerate(chunks, 1):
                                chunk_tokens = engine._count_tokens(chunk)
                                st.text(f"Chunk {i} ({chunk_tokens}t): {chunk[:80]}...")
            except:
                pass

    if st.button("🎬 Process Script", type="primary", width="stretch"):
        if not script_text:
            st.error("❌ Please provide a script")
        else:
            try:
                engine = get_current_engine()

                if engine:
                    # Save script temporarily
                    script_dir = Path("temp/scripts")
                    script_dir.mkdir(parents=True, exist_ok=True)
                    script_path = script_dir / "temp_script.txt"

                    with open(script_path, "w", encoding="utf-8") as f:
                        f.write(script_text)

                    output_dir = Path("outputs/scripts")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / script_output_name

                    with st.spinner("🔊 Processing script..."):
                        start_time = time.time()

                        # Set output format
                        temp_config = engine.config
                        temp_config.output_format = script_output_format

                        # Prepare generation parameters
                        gen_params = {
                            "script_path": str(script_path),
                            "output_path": str(output_path),
                            "gap_duration": gap_duration,
                            "voice": script_voice,
                            "speed": script_speed,
                        }

                        # Add emotion parameter for Indic engine
                        if current_engine == "indic" and script_emotion:
                            gen_params["emotion"] = script_emotion

                        result_path = engine.process_script(**gen_params)

                        generation_time = time.time() - start_time

                    # Get audio info
                    audio, sr = sf.read(str(result_path))
                    duration = len(audio) / sr
                    file_size = result_path.stat().st_size

                    # Success message
                    st.success("✅ Script processed successfully!")

                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Duration", f"{duration:.1f}s")
                    with col2:
                        st.metric("File Size", f"{file_size/1024/1024:.2f} MB")
                    with col3:
                        st.metric("Generation Time", f"{generation_time:.1f}s")
                    with col4:
                        st.metric("Script Length", f"{len(script_text)} chars")

                    # Audio player
                    st.audio(str(result_path), format="audio/wav")

                    # Download button
                    with open(result_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Voiceover",
                            data=f,
                            file_name=script_output_name,
                            mime="audio/wav",
                            width="stretch",
                        )

                    # Add to history
                    add_to_history(
                        {
                            "type": "script",
                            "script_length": len(script_text),
                            "voice": script_voice,
                            "speed": script_speed,
                            "gap_duration": gap_duration,
                            "duration": duration,
                            "file_size": file_size,
                            "generation_time": generation_time,
                            "output_path": str(result_path),
                        }
                    )

            except Exception as e:
                show_exception(e, "Script processing failed")

# ==========================================
# TAB 4: PODCAST GENERATION
# ==========================================
with tab4:
    st.markdown("## 🎙️ Podcast Generation")
    st.markdown("Create multi-voice podcasts with different voices and speeds per segment")

    # Helper functions for segment management
    def add_podcast_segment():
        """Add a new podcast segment"""
        st.session_state.podcast_segment_counter += 1
        st.session_state.podcast_segments.append(
            {
                "id": st.session_state.podcast_segment_counter,
                "name": f"Segment {st.session_state.podcast_segment_counter}",
                "text": "",
                "voice": "am_michael",
                "speed": 1.0,
            }
        )

    def remove_podcast_segment(segment_id: int):
        """Remove a podcast segment by ID"""
        st.session_state.podcast_segments = [
            seg for seg in st.session_state.podcast_segments if seg["id"] != segment_id
        ]

    def move_segment_up(index: int):
        """Move segment up in the list"""
        if index > 0:
            segments = st.session_state.podcast_segments
            segments[index], segments[index - 1] = segments[index - 1], segments[index]

    def move_segment_down(index: int):
        """Move segment down in the list"""
        segments = st.session_state.podcast_segments
        if index < len(segments) - 1:
            segments[index], segments[index + 1] = segments[index + 1], segments[index]

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### Podcast Segments")

        if not st.session_state.podcast_segments:
            st.info("🎬 No segments yet. Click 'Add Segment' to start building your podcast!")
        else:
            # Display segments
            for idx, segment in enumerate(st.session_state.podcast_segments):
                with st.expander(
                    f"🎤 {segment['name']} ({segment['voice']} @ {segment['speed']}x)",
                    expanded=True,
                ):
                    seg_col1, seg_col2, seg_col3 = st.columns([2, 1, 1])

                    with seg_col1:
                        segment["name"] = st.text_input(
                            "Segment Name",
                            value=segment["name"],
                            key=f"pod_name_{segment['id']}",
                            help="Optional label for this segment",
                        )

                    with seg_col2:
                        segment["voice"] = st.selectbox(
                            "Voice",
                            options=ALL_VOICES,
                            index=ALL_VOICES.index(segment["voice"]),
                            key=f"pod_voice_{segment['id']}",
                        )

                    with seg_col3:
                        segment["speed"] = st.slider(
                            "Speed",
                            min_value=0.5,
                            max_value=2.0,
                            value=segment["speed"],
                            step=0.05,
                            key=f"pod_speed_{segment['id']}",
                        )

                    segment["text"] = st.text_area(
                        "Segment Text",
                        value=segment["text"],
                        height=100,
                        key=f"pod_text_{segment['id']}",
                        placeholder="Enter the text for this segment...",
                    )

                    # Segment actions
                    action_col1, action_col2, action_col3, action_col4 = st.columns(4)

                    with action_col1:
                        if st.button("⬆️ Move Up", key=f"pod_up_{segment['id']}"):
                            move_segment_up(idx)
                            st.rerun()

                    with action_col2:
                        if st.button("⬇️ Move Down", key=f"pod_down_{segment['id']}"):
                            move_segment_down(idx)
                            st.rerun()

                    with action_col3:
                        if st.button("🗑️ Remove", key=f"pod_remove_{segment['id']}"):
                            remove_podcast_segment(segment["id"])
                            st.rerun()

                    with action_col4:
                        char_count = len(segment["text"])
                        st.caption(f"📝 {char_count} chars")

    with col2:
        st.markdown("### Settings")

        podcast_gap = st.slider(
            "Gap Between Segments",
            min_value=0.0,
            max_value=3.0,
            value=0.6,
            step=0.1,
            help="Pause duration between segments",
        )

        podcast_enhance = st.checkbox(
            "Audio Enhancement",
            value=True,
            help="Apply normalization, noise reduction, and fades",
        )

        podcast_output = st.text_input(
            "Output Filename",
            value=f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
        )

        st.markdown("---")

        st.markdown("### Quick Actions")

        if st.button("➕ Add Segment", type="primary", use_container_width=True):
            add_podcast_segment()
            st.rerun()

        # Podcast Templates
        st.markdown("### 🎨 Templates")

        templates = {
            "Interview (2 Hosts)": [
                {
                    "id": 1,
                    "name": "AI Disclosure",
                    "text": "This podcast is created using Claude by Anthropic for content creation and Aparsoft TTS for voice synthesis.",
                    "voice": "am_michael",
                    "speed": 1.0,
                },
                {
                    "id": 2,
                    "name": "Host Intro",
                    "text": "Welcome to our podcast. Today we have a special guest.",
                    "voice": "am_michael",
                    "speed": 1.0,
                },
                {
                    "id": 3,
                    "name": "Guest Response",
                    "text": "Thanks for having me. I'm excited to be here.",
                    "voice": "af_bella",
                    "speed": 0.95,
                },
                {
                    "id": 4,
                    "name": "Host Question",
                    "text": "So tell us, what have you been working on lately?",
                    "voice": "am_michael",
                    "speed": 1.05,
                },
            ],
            "News Report": [
                {
                    "id": 1,
                    "name": "AI Disclosure",
                    "text": "This content is generated using AI technology.",
                    "voice": "af_sarah",
                    "speed": 1.0,
                },
                {
                    "id": 2,
                    "name": "Breaking News",
                    "text": "Breaking news today from the world of technology.",
                    "voice": "af_sarah",
                    "speed": 1.1,
                },
                {
                    "id": 3,
                    "name": "Details",
                    "text": "Here are the key details you need to know.",
                    "voice": "af_sarah",
                    "speed": 1.0,
                },
            ],
            "Storytelling": [
                {
                    "id": 1,
                    "name": "Opening",
                    "text": "Once upon a time, in a land far away...",
                    "voice": "bm_george",
                    "speed": 0.9,
                },
                {
                    "id": 2,
                    "name": "Chapter 1",
                    "text": "The hero began their journey at dawn.",
                    "voice": "bm_george",
                    "speed": 0.95,
                },
            ],
            "Tutorial": [
                {
                    "id": 1,
                    "name": "Intro",
                    "text": "Hello everyone! Today I'll show you step by step.",
                    "voice": "af_nicole",
                    "speed": 1.0,
                },
                {
                    "id": 2,
                    "name": "Step 1",
                    "text": "First, let's start with the basics.",
                    "voice": "af_nicole",
                    "speed": 0.95,
                },
            ],
        }

        selected_template = st.selectbox(
            "Choose Template",
            options=list(templates.keys()),
            key="podcast_template_select",
        )

        if st.button("📋 Load Template", use_container_width=True):
            # Load selected template
            st.session_state.podcast_segments = templates[selected_template]
            st.session_state.podcast_segment_counter = len(templates[selected_template])
            st.success(f"✅ Loaded template: {selected_template}")
            st.rerun()

        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.podcast_segments = []
            st.session_state.podcast_segment_counter = 0
            st.rerun()

        st.markdown("---")

        # Podcast info
        st.markdown("### 📊 Podcast Info")
        total_segments = len(st.session_state.podcast_segments)
        total_chars = sum(len(seg["text"]) for seg in st.session_state.podcast_segments)
        unique_voices = len(set(seg["voice"] for seg in st.session_state.podcast_segments))

        st.metric("Total Segments", total_segments)
        st.metric("Total Characters", total_chars)
        st.metric("Unique Voices", unique_voices)

    # Generate and Add Segment buttons at bottom
    st.markdown("---")

    # Create two columns for buttons
    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        add_segment_bottom = st.button(
            "➕ Add Segment", use_container_width=True, key="add_segment_bottom"
        )

    with btn_col2:
        generate_podcast = st.button(
            "🎧 Generate Podcast", type="primary", use_container_width=True
        )

    # Handle add segment button click
    if add_segment_bottom:
        add_podcast_segment()
        st.rerun()

    if generate_podcast:
        # Validate segments
        valid_segments = [seg for seg in st.session_state.podcast_segments if seg["text"].strip()]

        if not valid_segments:
            st.error("❌ No segments with text. Please add content to at least one segment.")
        else:
            try:
                engine = get_current_engine()

                if engine:
                    output_dir = Path("outputs/podcasts")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / podcast_output

                    with st.spinner("🎙️ Generating podcast..."):
                        start_time = time.time()

                        # Generate each segment
                        audio_segments = []
                        segment_details = []

                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        for i, segment in enumerate(valid_segments):
                            status_text.text(
                                f"🔊 Processing {i+1}/{len(valid_segments)}: {segment['name']}"
                            )

                            # Generate audio for this segment
                            audio = engine.generate(
                                text=segment["text"],
                                voice=segment["voice"],
                                speed=segment["speed"],
                                enhance=podcast_enhance,
                            )

                            audio_segments.append(audio)

                            # Get duration
                            duration = get_audio_duration(audio, engine.config.sample_rate)

                            segment_details.append(
                                {
                                    "name": segment["name"],
                                    "voice": segment["voice"],
                                    "speed": segment["speed"],
                                    "duration": duration,
                                    "chars": len(segment["text"]),
                                }
                            )

                            progress_bar.progress((i + 1) / len(valid_segments))

                        # Combine segments
                        status_text.text("🔧 Combining segments...")

                        from aparsoft_tts.utils.audio import combine_audio_segments, save_audio

                        combined_audio = combine_audio_segments(
                            audio_segments,
                            sample_rate=engine.config.sample_rate,
                            gap_duration=podcast_gap,
                        )

                        # Save
                        save_audio(
                            combined_audio,
                            str(output_path),
                            sample_rate=engine.config.sample_rate,
                        )

                        generation_time = time.time() - start_time
                        total_duration = get_audio_duration(
                            combined_audio, engine.config.sample_rate
                        )
                        file_size = output_path.stat().st_size

                        progress_bar.empty()
                        status_text.empty()

                    # Success message
                    st.success("✅ Podcast generated successfully!")

                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Total Duration", f"{total_duration:.1f}s")
                    with col2:
                        st.metric("File Size", f"{file_size/1024/1024:.2f} MB")
                    with col3:
                        st.metric("Generation Time", f"{generation_time:.1f}s")
                    with col4:
                        st.metric("Segments", len(valid_segments))

                    # Segment breakdown
                    st.markdown("### 🎙️ Segment Breakdown")

                    breakdown_df = pd.DataFrame(segment_details)
                    st.dataframe(breakdown_df, width="stretch", hide_index=True)

                    # Audio player
                    st.markdown("### 🎧 Preview Podcast")
                    st.audio(str(output_path), format="audio/wav")

                    # Download
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Podcast",
                            data=f,
                            file_name=podcast_output,
                            mime="audio/wav",
                            use_container_width=True,
                        )

                    # Add to history
                    add_to_history(
                        {
                            "type": "podcast",
                            "num_segments": len(valid_segments),
                            "voices_used": list(set(seg["voice"] for seg in valid_segments)),
                            "gap_duration": podcast_gap,
                            "enhance": podcast_enhance,
                            "duration": total_duration,
                            "file_size": file_size,
                            "generation_time": generation_time,
                            "output_path": str(output_path),
                        }
                    )

            except Exception as e:
                show_exception(e, "Podcast generation failed")

# ==========================================
# TAB 5: AUDIO TRANSCRIPTION
# ==========================================
with tab5:
    st.markdown("## 🎤 Audio Transcription (Speech-to-Text)")
    st.markdown("Transcribe audio files to text using OpenAI Whisper")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Audio Input")

        input_method = st.radio(
            "Input Method",
            options=["Upload Audio", "Select from Filesystem"],
            horizontal=True,
            key="stt_input_method",
        )

        audio_file_path = None

        if input_method == "Upload Audio":
            uploaded_audio = st.file_uploader(
                "Upload audio file",
                type=["wav", "mp3", "mp4", "mpeg", "mpga", "m4a", "webm"],
                help="Supported formats: WAV, MP3, MP4, MPEG, MPGA, M4A, WEBM",
            )

            if uploaded_audio:
                # Save uploaded file temporarily
                temp_dir = Path("temp/uploads")
                temp_dir.mkdir(parents=True, exist_ok=True)
                audio_file_path = temp_dir / uploaded_audio.name

                with open(audio_file_path, "wb") as f:
                    f.write(uploaded_audio.getbuffer())

                st.success(f"✅ Loaded: {uploaded_audio.name}")

                # Show audio player
                st.audio(str(audio_file_path))

        else:
            audio_path_input = st.text_input(
                "Enter audio file path",
                placeholder="/path/to/audio.wav",
                help="Enter absolute or relative path to audio file",
            )

            if audio_path_input:
                audio_file_path = Path(audio_path_input)

                if audio_file_path.exists():
                    st.success(f"✅ File found: {audio_file_path.name}")
                    try:
                        st.audio(str(audio_file_path))
                    except:
                        st.warning(
                            "⚠️ Unable to preview audio (format may not be supported for web playback)"
                        )
                else:
                    st.error(f"❌ File not found: {audio_file_path}")
                    audio_file_path = None

    with col2:
        st.markdown("### Settings")

        model_size = st.selectbox(
            "Whisper Model",
            options=["tiny", "base", "small", "medium", "large"],
            index=1,  # Default to 'base'
            help="Larger models = better accuracy but slower",
        )

        # Model info
        model_info = {
            "tiny": "39M params, ~1GB RAM, Fastest",
            "base": "74M params, ~1GB RAM, Recommended",
            "small": "244M params, ~2GB RAM, Balanced",
            "medium": "769M params, ~5GB RAM, High accuracy",
            "large": "1550M params, ~10GB RAM, Best accuracy",
        }
        st.info(f"📊 {model_info[model_size]}")

        language = st.text_input(
            "Language (optional)",
            placeholder="en, es, fr, etc.",
            help="Leave empty for automatic detection",
        )

        task = st.selectbox(
            "Task",
            options=["transcribe", "translate"],
            help="transcribe = same language, translate = to English",
        )

        transcript_filename = st.text_input(
            "Output filename",
            value=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )

        st.markdown("---")
        st.markdown("### 📖 Model Guide")
        with st.expander("Click for model recommendations"):
            st.markdown(
                """
            **tiny**: Quick testing  
            **base**: Most use cases 🌟  
            **small**: Balanced quality  
            **medium**: Professional work  
            **large**: Maximum accuracy  
            """
            )

    # Transcribe button
    st.markdown("---")

    if st.button("🎙️ Transcribe Audio", type="primary", use_container_width=True):
        if not audio_file_path:
            st.error("❌ Please provide an audio file")
        else:
            try:
                # Check if Whisper is installed
                try:
                    import whisper
                except ImportError:
                    st.error(
                        """
                    ❌ OpenAI Whisper is not installed!
                    
                    To use speech-to-text functionality, install it with:
                    ```
                    pip install openai-whisper
                    ```
                    
                    Also ensure ffmpeg is installed on your system:
                    - Ubuntu/Debian: `sudo apt-get install ffmpeg`
                    - macOS: `brew install ffmpeg`
                    - Windows: Download from https://ffmpeg.org/download.html
                    """
                    )
                    st.stop()

                from aparsoft_tts.utils.audio import transcribe_audio

                output_dir = Path("outputs/transcripts")
                output_dir.mkdir(parents=True, exist_ok=True)
                transcript_path = output_dir / transcript_filename

                with st.spinner(f"🔊 Transcribing with {model_size} model..."):
                    start_time = time.time()

                    result = transcribe_audio(
                        audio_path=str(audio_file_path),
                        output_path=str(transcript_path),
                        model_size=model_size,
                        language=language if language else None,
                        task=task,
                    )

                    transcription_time = time.time() - start_time

                # Success message
                st.success("✅ Transcription completed successfully!")

                # Metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Text Length", f"{len(result['text'])} chars")
                with col2:
                    st.metric("Word Count", f"~{len(result['text'].split())} words")
                with col3:
                    st.metric("Language", result["language"].upper())
                with col4:
                    st.metric("Time Taken", f"{transcription_time:.1f}s")

                # Display transcription
                st.markdown("### 📝 Transcription")
                st.text_area(
                    "Transcribed Text",
                    value=result["text"],
                    height=200,
                    help="Copy or edit the transcription",
                )

                # Timestamped segments
                if result["segments"]:
                    st.markdown("### ⏱️ Timestamped Segments")

                    with st.expander(f"View {len(result['segments'])} segments"):
                        for i, segment in enumerate(result["segments"], 1):
                            start = segment["start"]
                            end = segment["end"]
                            text = segment["text"].strip()
                            st.text(f"[{start:6.1f}s - {end:6.1f}s] {text}")

                # Download button
                with open(transcript_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="💾 Download Transcript",
                        data=f.read(),
                        file_name=transcript_filename,
                        mime="text/plain",
                        use_container_width=True,
                    )

                # Add to history
                add_to_history(
                    {
                        "type": "transcription",
                        "model_size": model_size,
                        "language": result["language"],
                        "task": task,
                        "text_length": len(result["text"]),
                        "word_count": len(result["text"].split()),
                        "segments": len(result["segments"]),
                        "transcription_time": transcription_time,
                        "audio_file": str(audio_file_path.name),
                        "output_path": str(transcript_path),
                    }
                )

            except Exception as e:
                show_exception(e, "Transcription failed")

# ==========================================
# TAB 6: VOICE EXPLORER
# ==========================================
with tab6:
    st.markdown("## 🔍 Voice Explorer")
    st.markdown("Compare and explore all available voices")

    # Batch Voice Comparison Tool
    st.markdown("### 🎭 Batch Voice Comparison")
    st.markdown("Generate the same text with ALL voices for easy comparison")

    batch_comparison_text = st.text_area(
        "Enter text to compare across all voices",
        value="Welcome to our podcast. This is a demonstration of high-quality text-to-speech.",
        height=80,
        key="batch_comparison_text",
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        voice_filter = st.multiselect(
            "Select voices to compare (leave empty for all)",
            options=ALL_VOICES,
            default=[],
            help="Select specific voices or leave empty to generate all",
        )

    with col2:
        comparison_speed = st.slider(
            "Speed",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            key="comparison_speed",
        )

    if st.button("🎤 Generate All Voice Comparisons", type="primary", use_container_width=True):
        if not batch_comparison_text:
            st.error("❌ Please enter text for comparison")
        else:
            try:
                engine = get_current_engine()

                if engine:
                    output_dir = Path("outputs/voice_comparison")
                    output_dir.mkdir(parents=True, exist_ok=True)

                    voices_to_compare = voice_filter if voice_filter else ALL_VOICES

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    generated_voices = []

                    for i, voice in enumerate(voices_to_compare):
                        status_text.text(
                            f"🔊 Generating {voice} ({i+1}/{len(voices_to_compare)})..."
                        )

                        output_path = output_dir / f"{voice}_comparison.wav"

                        engine.generate(
                            text=batch_comparison_text,
                            output_path=str(output_path),
                            voice=voice,
                            speed=comparison_speed,
                            enhance=True,
                        )

                        generated_voices.append({"voice": voice, "path": output_path})
                        progress_bar.progress((i + 1) / len(voices_to_compare))

                    progress_bar.empty()
                    status_text.empty()

                    st.success(f"✅ Generated {len(generated_voices)} voice samples!")

                    # Display all voices with audio players
                    st.markdown("### 🎵 Voice Samples")

                    # Organize by gender
                    st.markdown("#### 👨 Male Voices")
                    for item in generated_voices:
                        if item["voice"] in MALE_VOICES:
                            with st.expander(f"🎤 {item['voice']}", expanded=True):
                                st.audio(str(item["path"]), format="audio/wav")

                    st.markdown("#### 👩 Female Voices")
                    for item in generated_voices:
                        if item["voice"] in FEMALE_VOICES:
                            with st.expander(f"🎤 {item['voice']}", expanded=True):
                                st.audio(str(item["path"]), format="audio/wav")

            except Exception as e:
                show_exception(e, "Batch voice comparison failed")

    st.markdown("---")

    # Individual Voice Testing
    st.markdown("### Voice Testing")

    comparison_text = st.text_area(
        "Enter text for individual voice testing",
        value="Welcome to Aparsoft TTS. This is a demonstration of kokora-powered open-source text-to-speech capabilities.",
        height=100,
        key="individual_comparison_text",
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 👨 Male Voices")
        for voice in MALE_VOICES:
            with st.expander(f"🎤 {voice}"):
                st.markdown(f"**Voice:** {voice}")
                st.markdown("**Characteristics:**")

                voice_info = {
                    "am_adam": "American male - Natural inflection, conversational",
                    "am_michael": "American male - Professional, deep tones ⭐",
                    "bm_george": "British male - Classic, authoritative",
                    "bm_lewis": "British male - Modern, clear",
                }

                st.info(voice_info.get(voice, "Professional voice"))

                if st.button(f"Generate Sample", key=f"male_{voice}"):
                    try:
                        engine = get_current_engine()

                        if engine:
                            output_dir = Path("outputs/voice_samples")
                            output_dir.mkdir(parents=True, exist_ok=True)
                            output_path = output_dir / f"sample_{voice}.wav"

                            with st.spinner(f"Generating {voice}..."):
                                engine.generate(
                                    text=comparison_text,
                                    output_path=str(output_path),
                                    voice=voice,
                                    speed=1.0,
                                    enhance=True,
                                )

                            st.audio(str(output_path), format="audio/wav")
                            st.success("✅ Generated!")

                    except Exception as e:
                        show_exception(e, f"Voice sample generation failed for {voice}")

    with col2:
        st.markdown("#### 👩 Female Voices")
        for voice in FEMALE_VOICES:
            with st.expander(f"🎤 {voice}"):
                st.markdown(f"**Voice:** {voice}")
                st.markdown("**Characteristics:**")

                voice_info = {
                    "af_bella": "American female - Warm, friendly tones",
                    "af_nicole": "American female - Dynamic, expressive",
                    "af_sarah": "American female - Clear articulation",
                    "af_sky": "American female - Youthful, energetic",
                    "bf_emma": "British female - Professional, elegant",
                    "bf_isabella": "British female - Soft, gentle",
                }

                st.info(voice_info.get(voice, "Professional voice"))

                if st.button(f"Generate Sample", key=f"female_{voice}"):
                    try:
                        engine = get_current_engine()

                        if engine:
                            output_dir = Path("outputs/voice_samples")
                            output_dir.mkdir(parents=True, exist_ok=True)
                            output_path = output_dir / f"sample_{voice}.wav"

                            with st.spinner(f"Generating {voice}..."):
                                engine.generate(
                                    text=comparison_text,
                                    output_path=str(output_path),
                                    voice=voice,
                                    speed=1.0,
                                    enhance=True,
                                )

                            st.audio(str(output_path), format="audio/wav")
                            st.success("✅ Generated!")

                    except Exception as e:
                        show_exception(e, f"Voice sample generation failed for {voice}")

# ==========================================
# TAB 7: AUDIO FILE MANAGER
# ==========================================
with tab7:
    st.markdown("## 📁 Audio File Manager")
    st.markdown("Browse, play, and manage your generated audio files")

    # List all output directories
    output_dirs = {
        "Single Generations": "outputs/single",
        "Batch Generations": "outputs/batch",
        "Scripts": "outputs/scripts",
        "Podcasts": "outputs/podcasts",
        "Voice Comparisons": "outputs/voice_comparison",
        "Voice Samples": "outputs/voice_samples",
    }

    # Statistics
    total_files = 0
    total_size = 0

    for dir_path in output_dirs.values():
        dir_path = Path(dir_path)
        if dir_path.exists():
            files = list(dir_path.glob("*.*"))
            total_files += len(files)
            total_size += sum(f.stat().st_size for f in files)

    # Display stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", total_files)
    with col2:
        st.metric("Total Size", f"{total_size / (1024 * 1024):.1f} MB")
    with col3:
        st.metric("Directories", len([d for d in output_dirs.values() if Path(d).exists()]))

    st.markdown("---")

    # Bulk actions
    st.markdown("### 🧹 Bulk Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Export All as ZIP", use_container_width=True):
            st.info("🚧 ZIP export feature coming soon!")

    with col2:
        if st.button("🗑️ Clear All Files", use_container_width=True, type="secondary"):
            if st.session_state.get("confirm_delete_all"):
                deleted_count = 0
                for dir_path in output_dirs.values():
                    dir_path = Path(dir_path)
                    if dir_path.exists():
                        for file in dir_path.glob("*.*"):
                            file.unlink()
                            deleted_count += 1
                st.success(f"✅ Deleted {deleted_count} files!")
                st.session_state["confirm_delete_all"] = False
                st.rerun()
            else:
                st.session_state["confirm_delete_all"] = True
                st.warning("⚠️ Click again to confirm deletion of ALL files!")

    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # File browser by directory
    st.markdown("### 📂 File Browser")

    for category, dir_path in output_dirs.items():
        dir_path = Path(dir_path)

        if dir_path.exists():
            files = sorted(
                list(dir_path.glob("*.*")), key=lambda x: x.stat().st_mtime, reverse=True
            )

            if files:
                with st.expander(f"📁 {category} ({len(files)} files)", expanded=False):
                    for file in files:
                        file_stat = file.stat()
                        size_mb = file_stat.st_size / (1024 * 1024)
                        modified = datetime.fromtimestamp(file_stat.st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )

                        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

                        with col1:
                            st.text(file.name)

                        with col2:
                            st.text(f"{size_mb:.2f} MB")

                        with col3:
                            st.text(modified)

                        with col4:
                            # Play button
                            if file.suffix.lower() in [".wav", ".mp3", ".flac"]:
                                st.audio(str(file), format=f"audio/{file.suffix[1:]}")

                        with col5:
                            # Delete button
                            if st.button("🗑️", key=f"delete_{file.stem}_{file.parent.name}"):
                                file.unlink()
                                st.rerun()

                        # Download button for each file
                        with open(file, "rb") as f:
                            st.download_button(
                                label=f"📥 Download {file.name}",
                                data=f,
                                file_name=file.name,
                                mime=f"audio/{file.suffix[1:]}",
                                key=f"download_{file.stem}_{file.parent.name}",
                            )

                        st.markdown("---")
            else:
                with st.expander(f"📁 {category} (0 files)"):
                    st.info("📦 No files in this directory")
        else:
            with st.expander(f"📁 {category} (directory not created yet)"):
                st.info("📍 Directory will be created when you generate audio")

# ==========================================
# TAB 8: CONFIGURATION
# ==========================================
with tab8:
    st.markdown("## ⚙️ Configuration")
    st.markdown("Manage TTS engine and system settings")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎤 TTS Settings")

        config_voice = st.selectbox(
            "Default Voice",
            options=ALL_VOICES,
            index=ALL_VOICES.index("am_michael"),
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
                value=30.0,
                step=5.0,
                key="config_trim_db",
                help="Higher = less aggressive trimming, better preserves soft endings",
            )

        config_fade = st.slider(
            "Fade Duration (seconds)",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.05,
            key="config_fade",
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
            help="Normalize volume levels",
        )

        config_noise_reduction = st.checkbox(
            "Noise Reduction",
            value=True,
            key="config_noise_reduction",
            help="Apply spectral noise reduction",
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
                trim_db=config_trim_db if config_trim else 30.0,
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

    if st.session_state.engine:
        config = st.session_state.engine.config

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

# ==========================================
# TAB 9: ANALYTICS
# ==========================================
with tab9:
    st.markdown("## 📊 Analytics & History")
    st.markdown("Track and analyze your TTS generation activity")

    if not st.session_state.generation_history:
        st.info("📭 No generation history yet. Start generating audio to see analytics!")

    else:
        df = get_history_df()

        # Summary metrics
        st.markdown("### 📈 Summary Metrics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                """
            <div class='metric-card'>
                <h3>{}</h3>
                <p>Total Generations</p>
            </div>
            """.format(
                    len(df)
                ),
                unsafe_allow_html=True,
            )

        with col2:
            total_duration = df["duration"].sum() if "duration" in df.columns else 0
            st.markdown(
                """
            <div class='metric-card'>
                <h3>{:.1f}s</h3>
                <p>Total Audio Duration</p>
            </div>
            """.format(
                    total_duration
                ),
                unsafe_allow_html=True,
            )

        with col3:
            avg_gen_time = df["generation_time"].mean() if "generation_time" in df.columns else 0
            st.markdown(
                """
            <div class='metric-card'>
                <h3>{:.2f}s</h3>
                <p>Avg Generation Time</p>
            </div>
            """.format(
                    avg_gen_time
                ),
                unsafe_allow_html=True,
            )

        with col4:
            # Calculate unique voices using utility function
            voice_data = extract_voices_from_history(df)
            unique_voices = len(set(voice_data))

            st.markdown(
                """
            <div class='metric-card'>
                <h3>{}</h3>
                <p>Voices Used</p>
            </div>
            """.format(
                    unique_voices
                ),
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📊 Generations by Type")

            type_counts = df["type"].value_counts()

            fig = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Generation Type Distribution",
                color_discrete_sequence=px.colors.sequential.Purples_r,
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("### 🎤 Voice Usage")

            # Extract voices from history (handles both single and multi-voice)
            voice_data = extract_voices_from_history(df)

            if voice_data:
                voice_counts = pd.Series(voice_data).value_counts()

                fig = px.bar(
                    x=voice_counts.index,
                    y=voice_counts.values,
                    title="Voice Usage Count",
                    labels={"x": "Voice", "y": "Count"},
                    color=voice_counts.values,
                    color_continuous_scale="Purples",
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No voice data available yet")

        # Timeline
        st.markdown("### 📅 Generation Timeline")

        timeline_df = df.copy()
        timeline_df["date"] = timeline_df["timestamp"].dt.date
        daily_counts = timeline_df.groupby("date").size().reset_index(name="count")

        fig = px.line(
            daily_counts,
            x="date",
            y="count",
            title="Daily Generation Activity",
            labels={"date": "Date", "count": "Generations"},
            markers=True,
        )

        fig.update_traces(line_color="#667eea")

        st.plotly_chart(fig, use_container_width=True)

        # Recent History Table
        st.markdown("### 📜 Recent History")

        # Select columns that exist in the dataframe
        available_cols = [
            "timestamp",
            "type",
            "voice",
            "voices_used",
            "duration",
            "generation_time",
        ]
        display_cols = [col for col in available_cols if col in df.columns]

        if display_cols:
            recent_df = df[display_cols].tail(10).sort_values("timestamp", ascending=False)

            # Normalize voice columns for display
            display_df = normalize_voice_column(recent_df)

            st.dataframe(display_df, width="stretch", hide_index=True)
        else:
            st.info("No history data available")

        # Export options
        st.markdown("---")
        st.markdown("### 📤 Export Data")

        col1, col2, col3 = st.columns(3)

        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"tts_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                width="stretch",
            )

        with col2:
            json_data = df.to_json(orient="records", indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f"tts_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                width="stretch",
            )

        with col3:
            if st.button("🗑️ Clear All History", width="stretch"):
                st.session_state.generation_history = []
                st.session_state.total_generations = 0
                st.rerun()

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.markdown(
    """
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p style='margin: 0;'>
        <strong>Aparsoft TTS Manager</strong> v1.0.0 | 
        Powered by <a href='https://huggingface.co/hexgrad/Kokoro-82M' target='_blank'>Kokoro-82M</a>
    </p>
    <p style='margin: 0.5rem 0 0 0;'>
        📧 contact@aparsoft.com | 
        🌐 <a href='https://aparsoft.com' target='_blank'>aparsoft.com</a>
    </p>
</div>
""",
    unsafe_allow_html=True,
)
