# aparsoft_tts/utils/audio.py

"""Audio processing utilities for TTS system.

This module provides various audio processing functions used in the Aparsoft TTS
system. It includes audio enhancement, combining segments, loading/saving audio,
chunking for streaming, duration calculation, and speech-to-text transcription using
OpenAI Whisper.

Key functionalities:
- Audio enhancement (normalization, trimming, noise reduction, fades)
- Combining audio segments with gaps and crossfades
- Loading and saving audio files
- Chunking audio for streaming
- Getting audio duration
- Transcribing audio to text using OpenAI Whisper
"""

from pathlib import Path
from typing import BinaryIO

import librosa
import numpy as np
import soundfile as sf
from numpy.typing import NDArray

from aparsoft_tts.utils.exceptions import AudioProcessingError
from aparsoft_tts.utils.logging import get_logger

log = get_logger(__name__)


def enhance_audio(
    audio: NDArray[np.float32],
    sample_rate: int = 24000,
    normalize: bool = True,
    trim_silence: bool = True,
    trim_db: float = 30.0,  # Conservative trimming (higher = less aggressive, better preserves soft endings)
    add_fade: bool = True,
    fade_duration: float = 0.1,
    noise_reduction: bool = True,
) -> NDArray[np.float32]:
    """Enhance audio quality using various processing techniques.

    Args:
        audio: Input audio array
        sample_rate: Audio sample rate in Hz
        normalize: Apply normalization
        trim_silence: Trim silence from beginning and end
        trim_db: dB threshold for silence trimming
        add_fade: Add fade in/out
        fade_duration: Fade duration in seconds
        noise_reduction: Apply spectral noise reduction

    Returns:
        Enhanced audio array

    Raises:
        AudioProcessingError: If audio processing fails

    Example:
        >>> audio = np.random.randn(24000)
        >>> enhanced = enhance_audio(audio)
    """
    try:
        log.debug(
            "enhancing_audio",
            audio_length=len(audio),
            sample_rate=sample_rate,
            normalize=normalize,
            trim_silence=trim_silence,
        )

        # Ensure audio is float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Normalize
        if normalize:
            audio = librosa.util.normalize(audio)

        # Trim silence with conservative parameters to preserve soft endings
        if trim_silence:
            # Use smaller frame/hop lengths for better resolution (prevents voice cutoff)
            audio_trimmed, trim_indices = librosa.effects.trim(
                audio,
                top_db=trim_db,
                frame_length=512,  # Smaller for better resolution (default 2048)
                hop_length=128,  # Smaller for finer control (default 512)
            )

            # Add generous margin at end to preserve soft endings (critical for am_michael voice)
            # This prevents cutting off final consonants and soft voice endings
            margin_samples = int(0.1 * sample_rate)  # 100ms margin at end (increased from 50ms)
            start_idx = trim_indices[0]
            end_idx = min(trim_indices[1] + margin_samples, len(audio))

            audio = audio[start_idx:end_idx]

        # Spectral noise reduction
        if noise_reduction:
            audio = _apply_noise_reduction(audio)

        # Add fade in/out
        if add_fade:
            audio = _apply_fade(audio, sample_rate, fade_duration)

        log.debug("audio_enhanced", output_length=len(audio))
        return audio

    except Exception as e:
        log.error("audio_enhancement_failed", error=str(e))
        raise AudioProcessingError(f"Failed to enhance audio: {e}") from e


def _apply_noise_reduction(audio: NDArray[np.float32]) -> NDArray[np.float32]:
    """Apply spectral noise reduction.

    Args:
        audio: Input audio array

    Returns:
        Noise-reduced audio array
    """
    # STFT
    stft = librosa.stft(audio)
    magnitude = np.abs(stft)
    phase = np.angle(stft)

    # Simple noise gate using percentile
    noise_floor = np.percentile(magnitude, 10)
    magnitude[magnitude < noise_floor] = 0

    # Reconstruct
    enhanced_stft = magnitude * np.exp(1j * phase)
    audio = librosa.istft(enhanced_stft, length=len(audio))

    return audio


def _apply_fade(
    audio: NDArray[np.float32], sample_rate: int, fade_duration: float
) -> NDArray[np.float32]:
    """Apply fade in/out to audio.

    Args:
        audio: Input audio array
        sample_rate: Sample rate in Hz
        fade_duration: Fade duration in seconds

    Returns:
        Audio with fades applied
    """
    fade_samples = int(fade_duration * sample_rate)
    fade_samples = min(fade_samples, len(audio) // 4)  # Max 25% of audio length

    # Fade in
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples)

    # Fade out
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    return audio


def combine_audio_segments(
    segments: list[NDArray[np.float32]],
    sample_rate: int = 24000,
    gap_duration: float = 0.5,
    crossfade_duration: float = 0.1,  # Increased from 0.05s for smoother transitions
) -> NDArray[np.float32]:
    """Combine multiple audio segments with gaps and smooth crossfades.

    Args:
        segments: List of audio arrays to combine
        sample_rate: Sample rate in Hz
        gap_duration: Gap duration between segments in seconds
        crossfade_duration: Crossfade duration in seconds (prevents abrupt cuts)

    Returns:
        Combined audio array

    Raises:
        AudioProcessingError: If combining fails

    Example:
        >>> seg1 = np.random.randn(24000)
        >>> seg2 = np.random.randn(24000)
        >>> combined = combine_audio_segments([seg1, seg2])
    """
    try:
        log.debug("combining_segments", num_segments=len(segments), gap_duration=gap_duration)

        if not segments:
            raise AudioProcessingError("No segments provided")

        # Apply smooth fade out/in to each segment to prevent clicks
        crossfade_samples = int(crossfade_duration * sample_rate)

        processed_segments = []
        for segment in segments:
            segment = segment.astype(np.float32).copy()

            # Apply gentle fade out at end (prevents abrupt cuts)
            if len(segment) > crossfade_samples:
                fade_out = np.linspace(1, 0, crossfade_samples)
                segment[-crossfade_samples:] *= fade_out

            # Apply gentle fade in at start (smooth beginning)
            if len(segment) > crossfade_samples:
                fade_in = np.linspace(0, 1, crossfade_samples)
                segment[:crossfade_samples] *= fade_in

            processed_segments.append(segment)

        # Combine with gaps
        combined = []
        gap = np.zeros(int(gap_duration * sample_rate), dtype=np.float32)

        for i, segment in enumerate(processed_segments):
            combined.append(segment)
            if i < len(processed_segments) - 1:  # No gap after last segment
                combined.append(gap)

        result = np.concatenate(combined)
        log.debug("segments_combined", output_length=len(result))
        return result

    except Exception as e:
        log.error("segment_combination_failed", error=str(e))
        raise AudioProcessingError(f"Failed to combine segments: {e}") from e


def save_audio(
    audio: NDArray[np.float32],
    output_path: Path | str,
    sample_rate: int = 24000,
    format: str = "wav",
) -> Path:
    """Save audio to file.

    Args:
        audio: Audio array to save
        output_path: Output file path
        sample_rate: Sample rate in Hz
        format: Audio format (wav, flac, mp3)

    Returns:
        Path to saved file

    Raises:
        AudioProcessingError: If saving fails

    Example:
        >>> audio = np.random.randn(24000)
        >>> path = save_audio(audio, "output.wav")
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        log.debug(
            "saving_audio",
            path=str(output_path),
            length=len(audio),
            sample_rate=sample_rate,
            format=format,
        )

        sf.write(output_path, audio, sample_rate, format=format.upper())

        log.info("audio_saved", path=str(output_path), size_bytes=output_path.stat().st_size)
        return output_path

    except Exception as e:
        log.error("audio_save_failed", path=str(output_path), error=str(e))
        raise AudioProcessingError(f"Failed to save audio: {e}") from e


def load_audio(
    file_path: Path | str, sample_rate: int | None = None
) -> tuple[NDArray[np.float32], int]:
    """Load audio from file.

    Args:
        file_path: Path to audio file
        sample_rate: Target sample rate (None = use file's native rate)

    Returns:
        Tuple of (audio array, sample rate)

    Raises:
        AudioProcessingError: If loading fails

    Example:
        >>> audio, sr = load_audio("input.wav")
    """
    try:
        file_path = Path(file_path)

        log.debug("loading_audio", path=str(file_path))

        audio, sr = librosa.load(file_path, sr=sample_rate)

        log.debug("audio_loaded", length=len(audio), sample_rate=sr)
        return audio.astype(np.float32), sr

    except Exception as e:
        log.error("audio_load_failed", path=str(file_path), error=str(e))
        raise AudioProcessingError(f"Failed to load audio: {e}") from e


def chunk_audio(
    audio: NDArray[np.float32], chunk_size: int = 1024, overlap: int = 0
) -> list[NDArray[np.float32]]:
    """Split audio into chunks for streaming/processing.

    Args:
        audio: Input audio array
        chunk_size: Size of each chunk
        overlap: Overlap between chunks

    Returns:
        List of audio chunks

    Example:
        >>> audio = np.random.randn(24000)
        >>> chunks = chunk_audio(audio, chunk_size=1024)
    """
    chunks = []
    step = chunk_size - overlap

    for i in range(0, len(audio), step):
        chunk = audio[i : i + chunk_size]
        if len(chunk) > 0:
            chunks.append(chunk)

    log.debug("audio_chunked", num_chunks=len(chunks), chunk_size=chunk_size, overlap=overlap)
    return chunks


def get_audio_duration(audio: NDArray[np.float32], sample_rate: int = 24000) -> float:
    """Get duration of audio in seconds.

    Args:
        audio: Audio array
        sample_rate: Sample rate in Hz

    Returns:
        Duration in seconds

    Example:
        >>> audio = np.random.randn(24000)
        >>> duration = get_audio_duration(audio)
        >>> print(f"{duration:.2f}s")
    """
    return len(audio) / sample_rate


def transcribe_audio(
    audio_path: Path | str,
    output_path: Path | str | None = None,
    model_size: str = "medium",
    language: str | None = None,
    task: str = "transcribe",
    device: str = "auto",
    compute_type: str = "default",
    beam_size: int = 5,
    vad_filter: bool = True,
    word_timestamps: bool = False,
    use_faster_whisper: bool = True,
    initial_prompt: str | None = None,
) -> dict:
    """Transcribe audio file to text using faster-whisper or OpenAI Whisper.

    This function uses faster-whisper by default (4x faster than openai-whisper)
    or falls back to OpenAI's Whisper model for speech-to-text transcription.

    faster-whisper advantages:
    - 4x faster than openai-whisper for same accuracy
    - Lower memory usage
    - 8-bit quantization support
    - Built-in VAD filtering
    - Word-level timestamps

    Installation:
    - faster-whisper: pip install faster-whisper
    - openai-whisper: pip install openai-whisper

    Args:
        audio_path: Path to audio file (wav, mp3, mp4, etc.)
        output_path: Optional path to save transcription as text file.
                    If None, returns transcription without saving.
        model_size: Whisper model size. Options:
                   - 'tiny': Fastest, least accurate (~1GB RAM)
                   - 'base': Fast, good accuracy (~1GB RAM) [DEFAULT]
                   - 'small': Balanced (~2GB RAM)
                   - 'medium': High accuracy (~5GB RAM)
                   - 'large', 'large-v2', 'large-v3': Best accuracy (~10GB RAM)
                   - 'turbo', 'large-v3-turbo': Fast with high accuracy (~6GB RAM)
                   - 'distil-large-v3': Compressed model (5.8x faster, 51% fewer params)
        language: Language code (e.g., 'en', 'es', 'fr', 'hi'). None = auto-detect
                 For Hindi, use 'hi' and set initial_prompt to force Devanagari script
        task: Task type: 'transcribe' (same language) or 'translate' (to English)
        device: Device to use: 'cpu', 'cuda', or 'auto' (default)
        compute_type: Computation type:
                     - 'default': Auto-select based on device
                     - 'int8': 8-bit quantization (faster, less memory)
                     - 'int8_float16': 8-bit with FP16 (GPU only)
                     - 'float16': FP16 (GPU only)
                     - 'float32': FP32 (CPU default)
        beam_size: Beam size for decoding (default: 5, higher = more accurate but slower)
        vad_filter: Use Voice Activity Detection to filter silence (default: True)
        word_timestamps: Return word-level timestamps (default: False)
        use_faster_whisper: Use faster-whisper if True, else use openai-whisper (default: True)
        initial_prompt: Text prompt to guide transcription style/script.
                       For Hindi in Devanagari: "यह एक हिंदी वाक्य है।"
                       For Urdu: "یہ ایک اردو جملہ ہے۔"
                       This forces Whisper to use the desired script.

    Returns:
        Dictionary containing:
        - 'text': Full transcription text
        - 'segments': List of timestamped segments (with words if word_timestamps=True)
        - 'language': Detected/specified language
        - 'language_probability': Confidence of language detection (faster-whisper only)

    Raises:
        AudioProcessingError: If transcription fails
        ImportError: If required package is not installed

    Example:
        >>> # Basic transcription with faster-whisper (default)
        >>> result = transcribe_audio("speech.wav")
        >>> print(result['text'])

        >>> # Save to file with GPU acceleration
        >>> result = transcribe_audio(
        ...     "speech.wav",
        ...     output_path="transcript.txt",
        ...     model_size="large-v3",
        ...     device="cuda",
        ...     compute_type="float16"
        ... )

        >>> # Word-level timestamps
        >>> result = transcribe_audio(
        ...     "speech.wav",
        ...     word_timestamps=True
        ... )
        >>> for seg in result['segments']:
        ...     for word in seg.get('words', []):
        ...         print(f"[{word['start']:.2f}s - {word['end']:.2f}s] {word['word']}")

        >>> # Use OpenAI Whisper instead
        >>> result = transcribe_audio(
        ...     "speech.wav",
        ...     use_faster_whisper=False
        ... )
    """
    try:
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise AudioProcessingError(f"Audio file not found: {audio_path}")

        log.info(
            "transcribing_audio",
            path=str(audio_path),
            model_size=model_size,
            language=language,
            task=task,
            engine="faster-whisper" if use_faster_whisper else "openai-whisper",
        )

        if use_faster_whisper:
            # Use faster-whisper (recommended)
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                raise ImportError(
                    "faster-whisper is required for fast transcription. "
                    "Install with: pip install faster-whisper\n"
                    "Or set use_faster_whisper=False to use openai-whisper"
                )

            # Auto-select compute type based on device
            if compute_type == "default":
                if device == "cuda" or (device == "auto" and _is_cuda_available()):
                    compute_type = "float16"
                else:
                    compute_type = "int8"

            # Auto-select device
            if device == "auto":
                device = "cuda" if _is_cuda_available() else "cpu"

            log.debug(
                "loading_faster_whisper_model",
                model_size=model_size,
                device=device,
                compute_type=compute_type,
            )

            # Load faster-whisper model
            # Models are automatically cached in ~/.cache/huggingface/hub/
            # and reused on subsequent calls - no configuration needed!
            model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                cpu_threads=4,
            )

            # Transcribe with faster-whisper
            log.debug("transcribing_with_faster_whisper", file=str(audio_path))

            # Auto-set initial prompt for Hindi to force Devanagari script
            if language == "hi" and initial_prompt is None:
                initial_prompt = "यह एक हिंदी वाक्य है। नमस्ते, आप कैसे हैं?"
                log.debug("auto_set_hindi_devanagari_prompt")

            segments_generator, info = model.transcribe(
                str(audio_path),
                language=language,
                task=task,
                beam_size=beam_size,
                vad_filter=vad_filter,
                word_timestamps=word_timestamps,
                initial_prompt=initial_prompt,
            )

            # Convert generator to list to get all segments
            segments_list = list(segments_generator)

            # Extract text and format segments
            transcription_text = " ".join([seg.text.strip() for seg in segments_list])
            detected_language = info.language
            language_probability = info.language_probability

            # Format segments for output
            formatted_segments = []
            for seg in segments_list:
                seg_dict = {
                    "id": seg.id,
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                }

                # Add word-level timestamps if requested
                if word_timestamps and hasattr(seg, "words"):
                    seg_dict["words"] = [
                        {
                            "start": word.start,
                            "end": word.end,
                            "word": word.word,
                            "probability": word.probability,
                        }
                        for word in seg.words
                    ]

                formatted_segments.append(seg_dict)

            log.info(
                "transcription_complete",
                text_length=len(transcription_text),
                language=detected_language,
                language_probability=f"{language_probability:.2%}",
                num_segments=len(formatted_segments),
                engine="faster-whisper",
            )

            result = {
                "text": transcription_text,
                "segments": formatted_segments,
                "language": detected_language,
                "language_probability": language_probability,
            }

        else:
            # Use OpenAI Whisper (fallback)
            try:
                import whisper
            except ImportError:
                raise ImportError(
                    "OpenAI Whisper is required. "
                    "Install with: pip install openai-whisper\n"
                    "Or set use_faster_whisper=True to use faster-whisper (recommended)"
                )

            # Suppress Whisper's verbose output
            import sys
            import os

            original_stderr = sys.stderr

            try:
                sys.stderr = open(os.devnull, "w")

                log.debug("loading_openai_whisper_model", model_size=model_size)
                model = whisper.load_model(model_size)

                log.debug("transcribing_with_openai_whisper", file=str(audio_path))

                # Auto-set initial prompt for Hindi to force Devanagari script
                if language == "hi" and initial_prompt is None:
                    initial_prompt = "यह एक हिंदी वाक्य है। नमस्ते, आप कैसे हैं?"
                    log.debug("auto_set_hindi_devanagari_prompt")

                openai_result = model.transcribe(
                    str(audio_path),
                    language=language,
                    task=task,
                    verbose=False,
                    initial_prompt=initial_prompt,
                )
            finally:
                sys.stderr.close()
                sys.stderr = original_stderr

            transcription_text = openai_result["text"].strip()
            detected_language = openai_result.get("language", language or "unknown")

            log.info(
                "transcription_complete",
                text_length=len(transcription_text),
                language=detected_language,
                num_segments=len(openai_result.get("segments", [])),
                engine="openai-whisper",
            )

            result = {
                "text": transcription_text,
                "segments": openai_result.get("segments", []),
                "language": detected_language,
            }

        # Save to file if output path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result["text"])

            log.info("transcription_saved", path=str(output_path))

        return result

    except ImportError:
        raise
    except Exception as e:
        log.error("transcription_failed", error=str(e), path=str(audio_path))
        raise AudioProcessingError(f"Failed to transcribe audio: {e}") from e


def _is_cuda_available() -> bool:
    """Check if CUDA is available for GPU acceleration."""
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False
