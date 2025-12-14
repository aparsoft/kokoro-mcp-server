import streamlit as st
import pandas as pd
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
    get_engine_capabilities,
    get_audio_stats,
)


# ==========================================
# TAB 2: BATCH PROCESSING (ENHANCED)
# ==========================================
def render_tab_batch():
    """Render the Batch Processing tab with concurrent processing support"""
    st.markdown("## 📦 Batch Processing")
    st.markdown("Generate multiple audio files with optional concurrent processing")

    # Show capability badge if concurrent is supported
    capabilities = get_engine_capabilities()
    if capabilities.get("supports_concurrent"):
        st.success("⚡ Concurrent processing available for faster batch generation!")

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
            format_func=get_voice_display_name if current_engine == "kokoro" else str,
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

        # Concurrent processing option
        st.markdown("---")
        st.markdown("### ⚡ Performance")

        use_concurrent = st.checkbox(
            "Use Concurrent Processing",
            value=capabilities.get("supports_concurrent", False),
            disabled=not capabilities.get("supports_concurrent", False),
            help="Process multiple texts in parallel (faster but uses more memory)",
        )

        if use_concurrent:
            max_workers = st.slider(
                "Max Workers",
                min_value=1,
                max_value=4,
                value=2,
                help="Number of parallel generation threads",
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

                    # Prepare output paths
                    output_paths = [
                        str(output_dir / f"{filename_prefix}_{i+1:03d}.wav")
                        for i in range(len(texts))
                    ]

                    if use_concurrent and hasattr(engine, "batch_generate_concurrent"):
                        # Use concurrent batch processing
                        status_text.text("⚡ Processing batch concurrently...")

                        def progress_callback(completed, total, current_text):
                            progress_bar.progress(completed / total)
                            status_text.text(
                                f"⚡ Generating {completed}/{total}: {current_text[:40]}..."
                            )

                        # Generate all at once using concurrent processing
                        results = engine.batch_generate_concurrent(
                            texts=texts,
                            output_paths=output_paths,
                            voice=batch_voice,
                            speed=batch_speed,
                            enhance=True,
                            max_workers=max_workers if use_concurrent else 1,
                        )

                        # Collect results
                        for i, (text, output_path) in enumerate(zip(texts, output_paths)):
                            output_file = Path(output_path)
                            if output_file.exists():
                                audio_stats = get_audio_stats(output_file)
                                duration = audio_stats.get("duration_seconds", 0)
                                total_duration += duration

                                generated_files.append(
                                    {
                                        "file": output_file.name,
                                        "text": text[:50] + "..." if len(text) > 50 else text,
                                        "duration": audio_stats.get("duration", "N/A"),
                                        "size": f"{output_file.stat().st_size/1024:.1f} KB",
                                        "peak": audio_stats.get("peak_db", "N/A"),
                                    }
                                )
                            progress_bar.progress((i + 1) / len(texts))
                    else:
                        # Sequential processing (fallback)
                        for i, text in enumerate(texts):
                            status_text.text(f"🔊 Generating {i+1}/{len(texts)}: {text[:50]}...")

                            output_file = Path(output_paths[i])

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

                            # Get audio stats
                            audio_stats = get_audio_stats(output_file)
                            duration = audio_stats.get("duration_seconds", 0)
                            total_duration += duration

                            generated_files.append(
                                {
                                    "file": output_file.name,
                                    "text": text[:50] + "..." if len(text) > 50 else text,
                                    "duration": audio_stats.get("duration", "N/A"),
                                    "size": f"{output_file.stat().st_size/1024:.1f} KB",
                                    "peak": audio_stats.get("peak_db", "N/A"),
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
                        rtf = generation_time / total_duration if total_duration > 0 else 0
                        st.metric("Real-Time Factor", f"{rtf:.2f}x")

                    # File list with enhanced info
                    st.markdown("### Generated Files")
                    df = pd.DataFrame(generated_files)
                    st.dataframe(df, use_container_width=True)

                    # Add to history
                    add_to_history(
                        {
                            "type": "batch",
                            "count": len(texts),
                            "voice": batch_voice,
                            "speed": batch_speed,
                            "duration": total_duration,
                            "generation_time": generation_time,
                            "output_dir": str(output_dir),
                            "concurrent": use_concurrent,
                        }
                    )

            except Exception as e:
                show_exception(e, "Batch processing failed")
