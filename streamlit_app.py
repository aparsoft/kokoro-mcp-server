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
from pathlib import Path
import sys
import warnings

# Suppress warnings from PyTorch and other libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Import UI components
from st_ui.styles import apply_custom_css
from st_ui.sidebar import render_sidebar

# Import tab rendering functions
from st_tabs.tab_single import render_tab_single
from st_tabs.tab_batch import render_tab_batch
from st_tabs.tab_script import render_tab_script
from st_tabs.tab_podcast import render_tab_podcast
from st_tabs.tab_transcript import render_tab_transcript
from st_tabs.tab_voices import render_tab_voices
from st_tabs.tab_files import render_tab_files
from st_tabs.tab_config import render_tab_config
from st_tabs.tab_analytics import render_tab_analytics

# Import helper functions
from st_utils.helper import load_history

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
# INITIALIZATION
# ==========================================
apply_custom_css()
load_history()
render_sidebar()

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

# Render each tab
with tab1:
    render_tab_single()

with tab2:
    render_tab_batch()

with tab3:
    render_tab_script()

with tab4:
    render_tab_podcast()

with tab5:
    render_tab_transcript()

with tab6:
    render_tab_voices()

with tab7:
    render_tab_files()

with tab8:
    render_tab_config()

with tab9:
    render_tab_analytics()

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
