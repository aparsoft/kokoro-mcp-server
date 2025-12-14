import streamlit as st
from pathlib import Path
import json
import sys
import warnings

# Suppress warnings from PyTorch and other libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aparsoft_tts.core.engine_factory import get_engine_info
from st_utils.helper import (
    get_current_engine,
    save_history,
    get_voices_by_category,
    get_engine_capabilities,
    get_history_summary,
)


# ==========================================
# SIDEBAR
# ==========================================
def render_sidebar():
    """Render the main sidebar with engine selection, presets, and quick actions"""
    with st.sidebar:
        st.markdown("### 🎙️ Aparsoft TTS")
        st.markdown("---")

        # Quick Stats (Enhanced)
        st.markdown("### 📊 Quick Stats")
        summary = get_history_summary()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Generations", summary["total_generations"])
        with col2:
            current_engine_type = st.session_state.current_engine_type
            is_loaded = current_engine_type in st.session_state.engine_cache
            st.metric("Engine", "✅" if is_loaded else "⏳")

        if summary["total_generations"] > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Duration", summary["total_duration"])
            with col2:
                if summary["most_used_voice"]:
                    st.metric("Top Voice", summary["most_used_voice"][:8])

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

        # Show engine info (Enhanced)
        try:
            engine_info = get_engine_info(selected_engine)
            capabilities = get_engine_capabilities()

            if engine_info:
                with st.expander("ℹ️ Engine Details", expanded=False):
                    st.markdown(f"**Name:** {engine_info.get('name', 'N/A')}")
                    st.markdown(f"**Description:** {engine_info.get('description', 'N/A')}")
                    st.markdown(f"**Model Size:** {engine_info.get('model_size', 'N/A')}")
                    st.markdown(f"**Languages:** {', '.join(engine_info.get('languages', []))}")
                    st.markdown(f"**Voices:** {capabilities.get('max_voices', 'N/A')}")

                    # Show capability badges
                    st.markdown("**Capabilities:**")
                    caps = []
                    if capabilities.get("supports_voice_mixing"):
                        caps.append("🎭 Voice Mixing")
                    if capabilities.get("supports_timestamps"):
                        caps.append("⏱️ Timestamps")
                    if capabilities.get("supports_streaming"):
                        caps.append("📡 Streaming")
                    if capabilities.get("supports_concurrent"):
                        caps.append("⚡ Concurrent")
                    st.markdown(" • ".join(caps) if caps else "Standard features")

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

        def load_presets_local():
            if presets_file.exists():
                with open(presets_file, "r") as f:
                    return json.load(f)
            return {}

        def save_presets_local(presets):
            presets_file.parent.mkdir(parents=True, exist_ok=True)
            with open(presets_file, "w") as f:
                json.dump(presets, f, indent=2)

        presets = load_presets_local()

        if presets:
            selected_preset = st.selectbox(
                "Load Preset",
                options=list(presets.keys()),
                key="preset_select",
            )

            if st.button("📥 Load", width="stretch"):
                preset = presets[selected_preset]
                st.success(f"✅ Loaded preset: {selected_preset}")
                st.info(
                    f"Voice: {preset.get('voice', 'N/A')} | Speed: {preset.get('speed', 'N/A')}"
                )
        else:
            st.info("📝 No presets saved yet")

        # Save current engine config as preset
        preset_name = st.text_input(
            "Preset Name", placeholder="My Podcast Setup", key="new_preset_name"
        )

        if st.button("💾 Save Current Config", width="stretch"):
            if preset_name:
                try:
                    engine = get_current_engine()
                    config = engine.config
                    presets[preset_name] = {
                        "voice": config.voice,
                        "speed": config.speed,
                        "enhance_audio": config.enhance_audio,
                        "sample_rate": config.sample_rate,
                        "output_format": config.output_format,
                        "trim_db": config.trim_db,
                    }
                    save_presets_local(presets)
                    st.success(f"✅ Saved preset: {preset_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to save preset: {str(e)}")
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

        # About (Enhanced with voice count)
        st.markdown("### ℹ️ About")

        # Get voice categories for count
        try:
            voice_cats = get_voices_by_category()
            total_voices = sum(len(v) for v in voice_cats.values())
        except:
            total_voices = 15

        st.markdown(
            f"""
        **Aparsoft TTS Manager**
        
        Enterprise-grade Text-to-Speech management interface powered by Kokoro-82M.
        
        - 🎤 {total_voices} Professional Voices
        - 🎭 Voice Mixing Support
        - 🔊 Advanced Audio Processing
        - 📦 Concurrent Batch Processing
        - 📊 Analytics Dashboard
        
        **Contact:**
        - 📧 contact@aparsoft.com
        - 🌐 aparsoft.com
        """
        )
