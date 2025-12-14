import streamlit as st
import pandas as pd
from pathlib import Path
import time
from datetime import datetime
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
from aparsoft_tts.utils.audio import format_duration

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
# TAB 4: PODCAST GENERATION
# ==========================================
def render_tab_podcast():
    """Render the Podcast Generation tab"""
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
