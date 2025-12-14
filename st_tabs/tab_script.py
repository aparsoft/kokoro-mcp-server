import streamlit as st
from pathlib import Path
import time
from datetime import datetime
import soundfile as sf
import sys
import warnings

# Suppress warnings from PyTorch and other libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aparsoft_tts.core.engine import (
    ALL_VOICES,
)

# Import error handling utilities
from streamlit_utils import (
    show_exception,
)

from st_utils.helper import (
    get_current_engine,
    add_to_history,
    get_voice_display_name,
    get_audio_stats,
)


# ==========================================
# TAB 3: SCRIPT PROCESSING
# ==========================================
def render_tab_script():
    """Render the Script Processing tab"""
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
