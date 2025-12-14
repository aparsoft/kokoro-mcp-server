import streamlit as st
from pathlib import Path
import sys
import warnings

# Suppress warnings from PyTorch and other libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aparsoft_tts.core.engine import (
    ALL_VOICES,
    MALE_VOICES,
    FEMALE_VOICES,
    VOICE_REGISTRY,
)

# Import error handling utilities
from streamlit_utils import (
    show_exception,
)

from st_utils.helper import (
    get_current_engine,
    get_voices_by_category,
    get_voice_display_name,
    validate_voice_mix,
    get_voice_info,
)


def render_voice_card(voice_id: str) -> None:
    """Render a detailed voice card with all metadata."""
    info = get_voice_info(voice_id)
    if not info:
        st.warning(f"No info for {voice_id}")
        return

    # Gender emoji
    emoji = "👨" if info.gender == "male" else "👩"

    with st.expander(f"{emoji} {voice_id} - {info.accent}", expanded=False):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**Description:** {info.description}")
            st.markdown(f"**Accent:** {info.accent}")
            st.markdown(f"**Gender:** {info.gender.title()}")
            st.markdown(f"**Language Code:** {info.lang_code}")

        with col2:
            # Generate sample button
            if st.button(f"🎤 Generate Sample", key=f"sample_{voice_id}"):
                try:
                    engine = get_current_engine()
                    if engine:
                        output_dir = Path("outputs/voice_samples")
                        output_dir.mkdir(parents=True, exist_ok=True)
                        output_path = output_dir / f"sample_{voice_id}.wav"

                        with st.spinner(f"Generating {voice_id}..."):
                            engine.generate(
                                text="Welcome to Aparsoft TTS. This is a demonstration of high-quality text-to-speech.",
                                output_path=str(output_path),
                                voice=voice_id,
                                speed=1.0,
                                enhance=True,
                            )

                        st.audio(str(output_path), format="audio/wav")
                        st.success("✅ Generated!")
                except Exception as e:
                    show_exception(e, f"Failed to generate sample for {voice_id}")


# ==========================================
# TAB 6: VOICE EXPLORER (ENHANCED)
# ==========================================
def render_tab_voices():
    """Render the Voice Explorer tab with enhanced features"""
    st.markdown("## 🔍 Voice Explorer")
    st.markdown("Compare and explore all available voices with detailed metadata")

    # Voice statistics
    st.markdown("### 📊 Voice Statistics")
    voice_cats = get_voices_by_category()

    cols = st.columns(len(voice_cats))
    for i, (category, voices) in enumerate(voice_cats.items()):
        with cols[i]:
            st.metric(category, len(voices))

    st.markdown("---")

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
            format_func=get_voice_display_name,
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

                    # Display organized by category
                    st.markdown("### 🎵 Voice Samples by Category")

                    for category, voices in voice_cats.items():
                        st.markdown(f"#### {category}")
                        for item in generated_voices:
                            if item["voice"] in voices:
                                info = get_voice_info(item["voice"])
                                desc = info.description if info else ""
                                with st.expander(
                                    f"🎤 {item['voice']} - {desc[:50]}", expanded=True
                                ):
                                    st.audio(str(item["path"]), format="audio/wav")

            except Exception as e:
                show_exception(e, "Batch voice comparison failed")

    st.markdown("---")

    # Voice Mixing Lab
    st.markdown("### 🧪 Voice Mixing Lab")
    st.markdown("Experiment with mixing multiple voices for unique sounds")

    col1, col2 = st.columns(2)

    with col1:
        primary_voice = st.selectbox(
            "Primary Voice",
            options=ALL_VOICES,
            format_func=get_voice_display_name,
            key="mix_primary",
        )

    with col2:
        secondary_voice = st.selectbox(
            "Secondary Voice",
            options=ALL_VOICES,
            format_func=get_voice_display_name,
            key="mix_secondary",
        )

    mix_ratio = st.slider(
        "Mix Ratio (Primary:Secondary)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1,
        help="0.0 = 100% Primary, 1.0 = 100% Secondary",
    )

    mix_text = st.text_input(
        "Test Text", value="This is a voice mixing demonstration.", key="mix_test_text"
    )

    if st.button("🎭 Generate Mixed Voice", key="generate_mix"):
        try:
            engine = get_current_engine()
            if engine:
                # Create mix specification
                primary_weight = 1.0 - mix_ratio
                secondary_weight = mix_ratio
                voice_spec = (
                    f"{primary_voice}*{primary_weight:.1f}+{secondary_voice}*{secondary_weight:.1f}"
                )

                output_dir = Path("outputs/voice_mixing")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"mix_{primary_voice}_{secondary_voice}.wav"

                with st.spinner("Generating mixed voice..."):
                    engine.generate(
                        text=mix_text,
                        output_path=str(output_path),
                        voice=voice_spec,
                        speed=1.0,
                        enhance=True,
                    )

                st.success(f"✅ Generated with mix: {voice_spec}")
                st.audio(str(output_path), format="audio/wav")

        except Exception as e:
            show_exception(e, "Voice mixing failed")

    st.markdown("---")

    # Individual Voice Explorer (Enhanced with voice registry)
    st.markdown("### 📖 Voice Directory")
    st.markdown("Detailed information about each voice")

    for category, voices in voice_cats.items():
        st.markdown(f"#### {category}")
        for voice_id in voices:
            render_voice_card(voice_id)
