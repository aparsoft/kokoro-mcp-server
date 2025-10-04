"""Audio processing utilities for TTS system."""

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
    trim_db: float = 30.0,  # Less aggressive trimming (was 20.0, higher = gentler)
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

        # Trim silence with gentler parameters
        if trim_silence:
            # Use smaller frame/hop lengths for better resolution (prevents voice cutoff)
            audio, _ = librosa.effects.trim(
                audio,
                top_db=trim_db,
                frame_length=512,   # Smaller for better resolution (default 2048)
                hop_length=128      # Smaller for finer control (default 512)
            )

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
