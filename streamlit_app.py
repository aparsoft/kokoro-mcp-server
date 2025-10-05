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

from aparsoft_tts import TTSEngine, TTSConfig, ALL_VOICES, MALE_VOICES, FEMALE_VOICES
from aparsoft_tts.utils.audio import enhance_audio, get_audio_duration
from aparsoft_tts.config import get_config

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
if "engine" not in st.session_state:
    st.session_state.engine = None

if "generation_history" not in st.session_state:
    st.session_state.generation_history = []

if "total_generations" not in st.session_state:
    st.session_state.total_generations = 0

if "total_duration" not in st.session_state:
    st.session_state.total_duration = 0.0

# ==========================================
# HELPER FUNCTIONS
# ==========================================


def initialize_engine(config: TTSConfig = None) -> TTSEngine:
    """Initialize TTS engine with optional custom config"""
    try:
        with st.spinner("🔄 Initializing TTS Engine..."):
            engine = TTSEngine(config=config)
            st.session_state.engine = engine
        return engine
    except Exception as e:
        st.error(f"❌ Failed to initialize engine: {str(e)}")
        return None


def get_engine() -> TTSEngine:
    """Get or create TTS engine instance"""
    if st.session_state.engine is None:
        return initialize_engine()
    return st.session_state.engine


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


def save_history():
    """Save history to JSON file"""
    history_file = Path("data/generation_history.json")
    history_file.parent.mkdir(parents=True, exist_ok=True)

    with open(history_file, "w") as f:
        json.dump(st.session_state.generation_history, f, indent=2)


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
        st.metric("Active Sessions", 1 if st.session_state.engine else 0)

    st.markdown("---")

    # Engine Status
    st.markdown("### ⚙️ Engine Status")

    if st.session_state.engine:
        st.success("✅ Engine Ready")
        if st.button("🔄 Reload Engine", width="stretch"):
            st.session_state.engine = None
            initialize_engine()
            st.rerun()
    else:
        st.warning("⏳ Engine Not Initialized")
        if st.button("🚀 Initialize Engine", width="stretch"):
            initialize_engine()
            st.rerun()

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

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "🎯 Single Generation",
        "📦 Batch Processing",
        "📄 Script Processing",
        "🔍 Voice Explorer",
        "⚙️ Configuration",
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

        voice = st.selectbox(
            "Voice",
            options=ALL_VOICES,
            index=ALL_VOICES.index("am_michael"),
            help="Select the voice for generation",
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

        output_name = st.text_input(
            "Output filename",
            value=f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
            help="Name for the output file",
        )

    if st.button("🎤 Generate Speech", type="primary", width="stretch"):
        if not text_input:
            st.error("❌ Please enter some text to convert")
        else:
            try:
                engine = get_engine()

                if engine:
                    output_dir = Path("outputs/single")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / output_name

                    with st.spinner("🔊 Generating speech..."):
                        start_time = time.time()

                        result_path = engine.generate(
                            text=text_input,
                            output_path=str(output_path),
                            voice=voice,
                            speed=speed,
                            enhance=enhance,
                        )

                        generation_time = time.time() - start_time

                    # Get audio info
                    audio, sr = sf.read(str(result_path))
                    duration = len(audio) / sr
                    file_size = result_path.stat().st_size

                    # Add to history
                    add_to_history(
                        {
                            "type": "single",
                            "text_length": len(text_input),
                            "voice": voice,
                            "speed": speed,
                            "enhance": enhance,
                            "duration": duration,
                            "file_size": file_size,
                            "generation_time": generation_time,
                            "output_path": str(result_path),
                        }
                    )

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
                st.error(f"❌ Generation failed: {str(e)}")

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

        batch_voice = st.selectbox(
            "Voice", options=ALL_VOICES, index=ALL_VOICES.index("am_michael"), key="batch_voice"
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
                engine = get_engine()

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

                        engine.generate(
                            text=text,
                            output_path=str(output_file),
                            voice=batch_voice,
                            speed=batch_speed,
                            enhance=True,
                        )

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
                st.error(f"❌ Batch generation failed: {str(e)}")

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

        script_voice = st.selectbox(
            "Voice", options=ALL_VOICES, index=ALL_VOICES.index("am_michael"), key="script_voice"
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

        script_output_name = st.text_input(
            "Output filename",
            value=f"voiceover_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
            key="script_output",
        )

    if st.button("🎬 Process Script", type="primary", width="stretch"):
        if not script_text:
            st.error("❌ Please provide a script")
        else:
            try:
                engine = get_engine()

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

                        result_path = engine.process_script(
                            script_path=str(script_path),
                            output_path=str(output_path),
                            gap_duration=gap_duration,
                            voice=script_voice,
                            speed=script_speed,
                        )

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
                st.error(f"❌ Script processing failed: {str(e)}")

# ==========================================
# TAB 4: VOICE EXPLORER
# ==========================================
with tab4:
    st.markdown("## 🔍 Voice Explorer")
    st.markdown("Compare and explore all available voices")

    # Voice comparison
    st.markdown("### Voice Comparison")

    comparison_text = st.text_area(
        "Enter text for voice comparison",
        value="Welcome to Aparsoft TTS. This is a demonstration of our text-to-speech capabilities.",
        height=100,
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
                        engine = get_engine()

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
                        st.error(f"❌ Failed: {str(e)}")

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
                        engine = get_engine()

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
                        st.error(f"❌ Failed: {str(e)}")

# ==========================================
# TAB 5: CONFIGURATION
# ==========================================
with tab5:
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

    if st.button("💾 Save Configuration", type="primary", width="stretch"):
        try:
            # Create custom config
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
            )

            # Save to file
            config_dir = Path("config")
            config_dir.mkdir(parents=True, exist_ok=True)

            config_file = config_dir / "custom_config.json"

            with open(config_file, "w") as f:
                json.dump(custom_config.model_dump(), f, indent=2)

            # Reinitialize engine with new config
            st.session_state.engine = None
            initialize_engine(custom_config)

            st.success("✅ Configuration saved and engine reloaded!")

        except Exception as e:
            st.error(f"❌ Failed to save configuration: {str(e)}")

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
# TAB 6: ANALYTICS
# ==========================================
with tab6:
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
            unique_voices = df["voice"].nunique() if "voice" in df.columns else 0
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

            voice_counts = df["voice"].value_counts()

            fig = px.bar(
                x=voice_counts.index,
                y=voice_counts.values,
                title="Voice Usage Count",
                labels={"x": "Voice", "y": "Count"},
                color=voice_counts.values,
                color_continuous_scale="Purples",
            )

            st.plotly_chart(fig, use_container_width=True)

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

        display_cols = ["timestamp", "type", "voice", "duration", "generation_time"]
        display_cols = [col for col in display_cols if col in df.columns]

        recent_df = df[display_cols].tail(10).sort_values("timestamp", ascending=False)

        st.dataframe(recent_df, width="stretch", hide_index=True)

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
