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
    VOICE_REGISTRY,
)

# Import error handling utilities
from streamlit_utils import (
    show_exception,
)

from st_utils.helper import (
    get_current_engine,
    add_to_history,
    get_voice_display_name,
    get_voices_by_category,
    validate_voice_mix,
    get_audio_stats,
    get_fade_curve_options,
    get_engine_capabilities,
)


# ==========================================
# TAB 1: SINGLE GENERATION
# ==========================================
def render_tab_single():
    """Render the Single Speech Generation tab"""
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
        capabilities = get_engine_capabilities()

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

        # Voice selection with categories (for Kokoro)
        if current_engine == "kokoro":
            voice_categories = get_voices_by_category()

            # Flatten for selectbox but show category info
            voice = st.selectbox(
                "Voice",
                options=voice_options,
                index=voice_options.index(default_voice) if default_voice in voice_options else 0,
                format_func=get_voice_display_name,
                help=f"Select the voice for generation ({current_engine} engine)",
            )

            # Voice mixing (new feature!)
            if capabilities.get("supports_voice_mixing"):
                with st.expander("🎭 Voice Mixing (Advanced)", expanded=False):
                    st.markdown("Mix multiple voices for unique sounds")
                    use_voice_mix = st.checkbox("Enable Voice Mixing", value=False)

                    if use_voice_mix:
                        voice_mix_input = st.text_input(
                            "Voice Mix Specification",
                            placeholder="af_sky+af_bella or af_sky*0.7+af_bella*0.3",
                            help="Use + for equal mix, *weight for weighted mix",
                        )

                        if voice_mix_input:
                            is_valid, message = validate_voice_mix(voice_mix_input)
                            if is_valid:
                                st.success(message)
                                voice = voice_mix_input  # Use the mix instead
                            else:
                                st.error(message)
        else:
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
            step=0.05,
            help="Speech speed multiplier",
        )

        enhance = st.checkbox(
            "Enable Audio Enhancement",
            value=True,
            help="Apply normalization, noise reduction, and fades",
        )

        # Advanced audio settings
        with st.expander("🎛️ Audio Settings", expanded=False):
            fade_options = get_fade_curve_options()
            fade_curve = st.selectbox(
                "Fade Curve",
                options=list(fade_options.keys()),
                index=0,
                help="Shape of fade in/out transitions",
            )

            trim_silence = st.checkbox("Trim Silence", value=True)
            noise_reduction = st.checkbox("Noise Reduction", value=True)

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
