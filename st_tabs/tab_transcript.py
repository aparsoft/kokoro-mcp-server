import streamlit as st
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


# Import error handling utilities
from streamlit_utils import (
    show_exception,
)

from st_utils.helper import add_to_history, get_audio_stats


# ==========================================
# TAB 5: AUDIO TRANSCRIPTION
# ==========================================
def render_tab_transcript():
    """Render the Audio Transcription tab"""
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
