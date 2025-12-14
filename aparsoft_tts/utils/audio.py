# aparsoft_tts/utils/audio.py

"""World-Class Audio Processing Utilities for TTS System.

This module provides production-grade audio processing functions using latest
best practices from noisereduce v3.0, librosa, and professional audio engineering.

Key Features:
- 🔇 Spectral Gating Noise Reduction (noisereduce v3.0 patterns)
- 🎛️ Stationary & Non-stationary noise handling
- 🎚️ Professional normalization with headroom
- ✂️ Intelligent silence trimming with voice-specific profiles
- 🔊 Smooth fade curves (linear, exponential, cosine)
- 🎵 Crossfade audio segment combination
- 📝 Speech-to-text transcription (faster-whisper/OpenAI Whisper)
- ⚡ GPU acceleration support (CUDA, TorchGate)
- 🌍 Multi-language transcription with script forcing

Audio Processing Pipeline:
    1. Pre-padding for soft attack voices
    2. Spectral noise reduction (n_fft=1024 for speech)
    3. Normalization with peak limiting
    4. Intelligent silence trimming
    5. Voice-specific fade curves

References:
    - https://github.com/timsainb/noisereduce (v3.0)
    - https://librosa.org/doc/latest/index.html
    - https://numpy.org/doc/stable/reference/routines.fft.html
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Literal, NamedTuple

import librosa
import numpy as np
import soundfile as sf
from numpy.typing import NDArray

from aparsoft_tts.utils.exceptions import AudioProcessingError
from aparsoft_tts.utils.logging import get_logger

log = get_logger(__name__)

# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

# Kokoro TTS sample rate (fixed by model architecture)
DEFAULT_SAMPLE_RATE = 24000

# Speech-optimized FFT parameters (from noisereduce best practices)
# n_fft=1024 recommended for speech (vs 2048 for music)
SPEECH_N_FFT = 1024
SPEECH_HOP_LENGTH = 256
SPEECH_WIN_LENGTH = 1024

# Noise reduction parameters (from noisereduce v3.0)
NOISE_REDUCTION_DEFAULTS = {
    "stationary": True,
    "prop_decrease": 0.95,  # How much to reduce noise (0-1)
    "freq_mask_smooth_hz": 500,  # Frequency smoothing
    "time_mask_smooth_ms": 50,  # Time smoothing
    "n_fft": SPEECH_N_FFT,
    "hop_length": SPEECH_HOP_LENGTH,
    "use_torch": False,  # Use TorchGate if available
}

# Voice-specific processing profiles
# SAFE defaults that preserve initial consonants
# KEY: We add padding BEFORE processing, never trim
VOICE_PROFILES = {
    "af_sarah": {
        "padding_start": 0.05,  # 50ms padding before speech (protective)
        "padding_end": 0.05,  # 50ms padding after speech
        "fade_out_duration": 0.08,  # Longer fade out for natural decay
    },
    "default": {
        "padding_start": 0.05,  # 50ms padding - just enough to prevent clicks
        "padding_end": 0.05,  # 50ms padding
        "fade_out_duration": 0.10,  # 100ms fade out for natural decay
    },
}


class FadeCurve(Enum):
    """Fade curve types for audio transitions."""

    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    COSINE = "cosine"  # S-curve, smoothest
    LOGARITHMIC = "logarithmic"


@dataclass
class AudioMetadata:
    """Metadata about an audio file or array."""

    duration: float
    sample_rate: int
    samples: int
    channels: int = 1
    peak_amplitude: float = 0.0
    rms_level: float = 0.0

    @property
    def duration_formatted(self) -> str:
        """Duration as MM:SS.mmm format."""
        mins = int(self.duration // 60)
        secs = self.duration % 60
        return f"{mins:02d}:{secs:06.3f}"


class TranscriptionSegment(NamedTuple):
    """A segment of transcribed audio with timing."""

    id: int
    start: float
    end: float
    text: str
    words: list[dict] = []


@dataclass
class TranscriptionResult:
    """Result from audio transcription."""

    text: str
    segments: list[TranscriptionSegment]
    language: str
    language_probability: float = 0.0
    engine: str = "faster-whisper"

    @property
    def word_count(self) -> int:
        """Total word count."""
        return len(self.text.split())


# =============================================================================
# AUDIO ENHANCEMENT FUNCTIONS
# =============================================================================


def get_voice_profile(voice_name: str | None) -> dict:
    """Get processing profile for a voice.

    Args:
        voice_name: Voice name (e.g., 'af_sarah')

    Returns:
        Dict of processing parameters
    """
    if voice_name and voice_name in VOICE_PROFILES:
        return VOICE_PROFILES[voice_name]
    return VOICE_PROFILES["default"]


def enhance_audio(
    audio: NDArray[np.float32],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    normalize: bool = True,
    trim_silence: bool = True,
    trim_db: float = 25.0,
    add_fade: bool = True,
    fade_duration: float = 0.1,
    noise_reduction: bool = True,
    voice_name: str | None = None,
    fade_curve: FadeCurve = FadeCurve.COSINE,
    headroom_db: float = -1.0,
) -> NDArray[np.float32]:
    """Enhance audio quality using professional processing techniques.

    Applies a SAFE audio enhancement pipeline that preserves speech onset:

    PIPELINE ORDER (critical for preserving initial consonants):
    1. Detect speech boundaries BEFORE any processing (energy-based onset)
    2. Add protective pre-padding to original audio
    3. Apply noise reduction (with padding protecting start)
    4. Normalize with headroom
    5. Apply minimal fade curves (anti-click only, ~10ms)

    KEY INSIGHT: We do NOT trim the audio. TTS output is already clean.
    The problem was trim cutting into speech. Instead, we just add padding
    and apply very gentle processing.

    Args:
        audio: Input audio array (any dtype, converted to float32)
        sample_rate: Audio sample rate in Hz
        normalize: Apply normalization with headroom
        trim_silence: (IGNORED - kept for API compatibility, we no longer trim)
        trim_db: (IGNORED - kept for API compatibility)
        add_fade: Add fade in/out (very short anti-click fades)
        fade_duration: Fade-out duration in seconds (fade-in is always ~10ms)
        noise_reduction: Apply gentle spectral noise reduction
        voice_name: Voice name for voice-specific processing
        fade_curve: Type of fade curve to use
        headroom_db: Headroom below 0dBFS for normalization (e.g., -1.0)

    Returns:
        Enhanced audio array (float32)

    Raises:
        AudioProcessingError: If audio processing fails

    Example:
        >>> audio = np.random.randn(24000).astype(np.float32)
        >>> enhanced = enhance_audio(audio, voice_name='af_sarah')
        >>> enhanced = enhance_audio(audio, fade_curve=FadeCurve.COSINE)
    """
    try:
        log.debug(
            "enhancing_audio",
            length=len(audio),
            sample_rate=sample_rate,
            voice_name=voice_name,
            normalize=normalize,
            noise_reduction=noise_reduction,
        )

        # Get voice-specific profile
        profile = get_voice_profile(voice_name)

        # Ensure float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # STEP 1: Add protective padding FIRST (BEFORE any processing!)
        # This ensures initial consonants are never touched
        padding_start = profile.get("padding_start", 0.05)
        padding_end = profile.get("padding_end", 0.05)
        audio = add_padding(audio, sample_rate, padding_start, padding_end)
        log.debug(
            "added_protective_padding_first",
            start_ms=int(padding_start * 1000),
            end_ms=int(padding_end * 1000),
        )

        # STEP 2: Apply GENTLE noise reduction (with padding protecting speech)
        if noise_reduction:
            audio = apply_noise_reduction(
                audio,
                sample_rate,
                prop_decrease=0.75,  # Gentler reduction to preserve transients
            )

        # STEP 3: Normalize with headroom
        if normalize:
            audio = normalize_audio(audio, headroom_db=headroom_db)

        # STEP 4: Apply MINIMAL fade curves (anti-click only, ~10ms)
        if add_fade:
            audio = apply_fade_asymmetric(
                audio,
                sample_rate,
                fade_in_duration=0.010,  # 10ms - just anti-click
                fade_out_duration=profile.get("fade_out_duration", fade_duration),
                curve=fade_curve,
            )

        log.debug("audio_enhanced", output_length=len(audio))
        return audio

    except Exception as e:
        log.error("audio_enhancement_failed", error=str(e))
        raise AudioProcessingError(f"Failed to enhance audio: {e}") from e


def apply_noise_reduction(
    audio: NDArray[np.float32],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    stationary: bool = True,
    prop_decrease: float = 0.95,
    n_fft: int = SPEECH_N_FFT,
    use_noisereduce: bool = True,
) -> NDArray[np.float32]:
    """Apply spectral gating noise reduction.

    Uses the noisereduce library's spectral gating algorithm if available,
    otherwise falls back to a simple STFT-based noise gate.

    The spectral gating algorithm (from Audacity) works by:
    1. Estimating noise profile from quiet sections
    2. Creating time-frequency mask based on SNR
    3. Applying smoothed mask to suppress noise

    Args:
        audio: Input audio array
        sample_rate: Sample rate in Hz
        stationary: Assume stationary noise (vs non-stationary)
        prop_decrease: Proportion to reduce noise (0-1)
        n_fft: FFT size (1024 recommended for speech)
        use_noisereduce: Try to use noisereduce library

    Returns:
        Noise-reduced audio array

    References:
        - https://github.com/timsainb/noisereduce
        - Spectral gating based on Audacity's noise reduction
    """
    # Try noisereduce library first
    if use_noisereduce:
        try:
            import noisereduce as nr

            log.debug("using_noisereduce_library", stationary=stationary)

            reduced = nr.reduce_noise(
                y=audio,
                sr=sample_rate,
                stationary=stationary,
                prop_decrease=prop_decrease,
                n_fft=n_fft,
                hop_length=n_fft // 4,
                freq_mask_smooth_hz=NOISE_REDUCTION_DEFAULTS["freq_mask_smooth_hz"],
                time_mask_smooth_ms=NOISE_REDUCTION_DEFAULTS["time_mask_smooth_ms"],
            )

            return reduced.astype(np.float32)

        except ImportError:
            log.debug("noisereduce_not_available_using_fallback")
        except Exception as e:
            log.warning("noisereduce_failed_using_fallback", error=str(e))

    # Fallback: Simple STFT-based noise gate
    return _apply_simple_noise_gate(audio, n_fft)


def _apply_simple_noise_gate(
    audio: NDArray[np.float32],
    n_fft: int = SPEECH_N_FFT,
    noise_percentile: float = 10.0,
) -> NDArray[np.float32]:
    """Apply simple STFT-based noise gate (fallback method).

    Uses percentile-based thresholding in the frequency domain.

    Args:
        audio: Input audio array
        n_fft: FFT size
        noise_percentile: Percentile for noise floor estimation

    Returns:
        Noise-gated audio
    """
    # STFT
    stft = librosa.stft(audio, n_fft=n_fft, hop_length=n_fft // 4)
    magnitude = np.abs(stft)
    phase = np.angle(stft)

    # Estimate noise floor from percentile
    noise_floor = np.percentile(magnitude, noise_percentile)

    # Simple soft gating
    gain = np.clip((magnitude - noise_floor) / (noise_floor + 1e-8), 0, 1)
    magnitude_reduced = magnitude * gain

    # Reconstruct
    enhanced_stft = magnitude_reduced * np.exp(1j * phase)
    result = librosa.istft(enhanced_stft, hop_length=n_fft // 4, length=len(audio))

    return result.astype(np.float32)


def normalize_audio(
    audio: NDArray[np.float32],
    headroom_db: float = -1.0,
    method: Literal["peak", "rms", "loudness"] = "peak",
) -> NDArray[np.float32]:
    """Normalize audio with professional headroom.

    Args:
        audio: Input audio array
        headroom_db: Target level below 0dBFS (e.g., -1.0)
        method: Normalization method:
                - 'peak': Normalize to peak amplitude
                - 'rms': Normalize to RMS level
                - 'loudness': Normalize to perceived loudness (LUFS)

    Returns:
        Normalized audio
    """
    if len(audio) == 0:
        return audio

    # Calculate target amplitude
    target_amplitude = 10 ** (headroom_db / 20)

    if method == "peak":
        # Peak normalization
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio * (target_amplitude / peak)

    elif method == "rms":
        # RMS normalization
        rms = np.sqrt(np.mean(audio**2))
        if rms > 0:
            # Target RMS ~0.1 for comfortable listening
            target_rms = 0.1 * target_amplitude
            audio = audio * (target_rms / rms)
            # Clip to prevent clipping
            audio = np.clip(audio, -1.0, 1.0)

    else:  # loudness
        # For LUFS, we'd need pyloudnorm - use peak as fallback
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio * (target_amplitude / peak)

    return audio.astype(np.float32)


def trim_audio_silence(
    audio: NDArray[np.float32],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    top_db: float = 30.0,
    margin_start: float = 0.05,
    margin_end: float = 0.10,
    frame_length: int = 512,
    hop_length: int = 128,
) -> NDArray[np.float32]:
    """Trim silence from audio with configurable margins.

    Uses librosa's trim function with fine-grained control for speech.

    Args:
        audio: Input audio array
        sample_rate: Sample rate in Hz
        top_db: Threshold in dB below reference (higher = less aggressive)
        margin_start: Margin to keep before speech (seconds)
        margin_end: Margin to keep after speech (seconds)
        frame_length: Frame length for energy calculation
        hop_length: Hop length for analysis

    Returns:
        Trimmed audio with margins
    """
    # Use smaller frame/hop for better resolution with speech
    audio_trimmed, trim_indices = librosa.effects.trim(
        audio,
        top_db=top_db,
        frame_length=frame_length,
        hop_length=hop_length,
    )

    # Add margins
    margin_start_samples = int(margin_start * sample_rate)
    margin_end_samples = int(margin_end * sample_rate)

    start_idx = max(trim_indices[0] - margin_start_samples, 0)
    end_idx = min(trim_indices[1] + margin_end_samples, len(audio))

    result = audio[start_idx:end_idx]

    log.debug(
        "audio_trimmed",
        original_length=len(audio),
        trimmed_length=len(result),
        margin_start_ms=int(margin_start * 1000),
        margin_end_ms=int(margin_end * 1000),
    )

    return result


def apply_fade(
    audio: NDArray[np.float32],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    fade_duration: float = 0.1,
    curve: FadeCurve = FadeCurve.COSINE,
    fade_in_start: float = 0.3,
) -> NDArray[np.float32]:
    """Apply fade in/out with configurable curve shape.

    Supports multiple fade curve types for different use cases:
    - LINEAR: Simple linear ramp
    - EXPONENTIAL: Quick start, slow finish (energetic)
    - COSINE: S-curve, smoothest transitions
    - LOGARITHMIC: Slow start, quick finish (natural decay)

    Args:
        audio: Input audio array
        sample_rate: Sample rate in Hz
        fade_duration: Fade duration in seconds
        curve: Type of fade curve
        fade_in_start: Starting volume for fade-in (0-1)

    Returns:
        Audio with fades applied
    """
    fade_samples = int(fade_duration * sample_rate)
    fade_samples = min(fade_samples, len(audio) // 4)  # Max 25% of audio

    if fade_samples <= 0:
        return audio

    audio = audio.copy()

    # Generate fade curve
    t = np.linspace(0, 1, fade_samples)

    if curve == FadeCurve.LINEAR:
        fade_in = np.linspace(fade_in_start, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)

    elif curve == FadeCurve.EXPONENTIAL:
        # Exponential: quick rise, plateau
        fade_in = fade_in_start + (1 - fade_in_start) * (1 - np.exp(-4 * t)) / (1 - np.exp(-4))
        fade_out = np.exp(-4 * t)

    elif curve == FadeCurve.COSINE:
        # Cosine: smooth S-curve (equal power)
        fade_in = fade_in_start + (1 - fade_in_start) * (1 - np.cos(np.pi * t)) / 2
        fade_out = (1 + np.cos(np.pi * t)) / 2

    else:  # LOGARITHMIC
        # Logarithmic: slow start, natural decay
        fade_in = fade_in_start + (1 - fade_in_start) * np.log1p(t * (np.e - 1)) / np.log(np.e)
        fade_out = 1 - np.log1p(t * (np.e - 1)) / np.log(np.e)

    # Apply fades
    audio[:fade_samples] *= fade_in.astype(np.float32)
    audio[-fade_samples:] *= fade_out.astype(np.float32)

    return audio


def apply_fade_asymmetric(
    audio: NDArray[np.float32],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    fade_in_duration: float = 0.015,
    fade_out_duration: float = 0.1,
    curve: FadeCurve = FadeCurve.COSINE,
) -> NDArray[np.float32]:
    """Apply asymmetric fade in/out with separate durations.

    This is optimized for TTS where:
    - Fade-in should be VERY SHORT (15-20ms) to prevent cutting initial consonants
    - Fade-out can be longer for natural decay

    The fade-in is purely for anti-click purposes, NOT volume reduction.
    Audio starts at full volume after a very brief attack.

    Args:
        audio: Input audio array
        sample_rate: Sample rate in Hz
        fade_in_duration: Fade-in duration (seconds) - keep SHORT!
        fade_out_duration: Fade-out duration (seconds)
        curve: Type of fade curve

    Returns:
        Audio with asymmetric fades applied
    """
    audio = audio.copy()

    # Calculate samples for each fade
    fade_in_samples = int(fade_in_duration * sample_rate)
    fade_out_samples = int(fade_out_duration * sample_rate)

    # Limit fade lengths to reasonable portions
    fade_in_samples = min(fade_in_samples, len(audio) // 10)  # Max 10% for fade-in
    fade_out_samples = min(fade_out_samples, len(audio) // 4)  # Max 25% for fade-out

    # Apply fade-in (very short, from 0 to 1)
    if fade_in_samples > 0:
        t_in = np.linspace(0, 1, fade_in_samples)

        if curve == FadeCurve.LINEAR:
            fade_in = t_in
        elif curve == FadeCurve.EXPONENTIAL:
            fade_in = (1 - np.exp(-4 * t_in)) / (1 - np.exp(-4))
        elif curve == FadeCurve.COSINE:
            fade_in = (1 - np.cos(np.pi * t_in)) / 2
        else:  # LOGARITHMIC
            fade_in = np.log1p(t_in * (np.e - 1)) / np.log(np.e)

        audio[:fade_in_samples] *= fade_in.astype(np.float32)

    # Apply fade-out (can be longer)
    if fade_out_samples > 0:
        t_out = np.linspace(0, 1, fade_out_samples)

        if curve == FadeCurve.LINEAR:
            fade_out = 1 - t_out
        elif curve == FadeCurve.EXPONENTIAL:
            fade_out = np.exp(-4 * t_out)
        elif curve == FadeCurve.COSINE:
            fade_out = (1 + np.cos(np.pi * t_out)) / 2
        else:  # LOGARITHMIC
            fade_out = 1 - np.log1p(t_out * (np.e - 1)) / np.log(np.e)

        audio[-fade_out_samples:] *= fade_out.astype(np.float32)

    return audio


def add_padding(
    audio: NDArray[np.float32],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    padding_start: float = 0.05,
    padding_end: float = 0.05,
) -> NDArray[np.float32]:
    """Add silent padding before and after audio.

    Prevents cutting off first/last characters in TTS output.

    Args:
        audio: Input audio array
        sample_rate: Sample rate in Hz
        padding_start: Padding at start (seconds)
        padding_end: Padding at end (seconds)

    Returns:
        Padded audio
    """
    start_pad = np.zeros(int(padding_start * sample_rate), dtype=np.float32)
    end_pad = np.zeros(int(padding_end * sample_rate), dtype=np.float32)

    return np.concatenate([start_pad, audio, end_pad])


# =============================================================================
# AUDIO SEGMENT COMBINATION
# =============================================================================


def combine_audio_segments(
    segments: list[NDArray[np.float32]],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    gap_duration: float = 0.5,
    crossfade_duration: float = 0.1,
    crossfade_curve: FadeCurve = FadeCurve.COSINE,
) -> NDArray[np.float32]:
    """Combine multiple audio segments with gaps and smooth crossfades.

    Uses equal-power crossfades for smooth transitions between segments.

    Args:
        segments: List of audio arrays to combine
        sample_rate: Sample rate in Hz
        gap_duration: Gap duration between segments (seconds)
        crossfade_duration: Crossfade duration (seconds)
        crossfade_curve: Curve type for crossfades

    Returns:
        Combined audio array

    Raises:
        AudioProcessingError: If combining fails

    Example:
        >>> seg1 = np.random.randn(24000).astype(np.float32)
        >>> seg2 = np.random.randn(24000).astype(np.float32)
        >>> combined = combine_audio_segments([seg1, seg2])
    """
    try:
        log.debug(
            "combining_segments",
            num_segments=len(segments),
            gap_duration=gap_duration,
            crossfade_duration=crossfade_duration,
        )

        if not segments:
            raise AudioProcessingError("No segments provided")

        if len(segments) == 1:
            return segments[0].astype(np.float32)

        crossfade_samples = int(crossfade_duration * sample_rate)

        # Process segments with crossfades
        processed = []
        for i, segment in enumerate(segments):
            segment = segment.astype(np.float32).copy()

            # Apply fade-out at end (except last segment)
            if i < len(segments) - 1 and len(segment) > crossfade_samples:
                fade_out = _get_fade_curve(crossfade_samples, crossfade_curve, fade_in=False)
                segment[-crossfade_samples:] *= fade_out

            # Apply fade-in at start (except first segment)
            if i > 0 and len(segment) > crossfade_samples:
                fade_in = _get_fade_curve(crossfade_samples, crossfade_curve, fade_in=True)
                segment[:crossfade_samples] *= fade_in

            processed.append(segment)

        # Combine with gaps
        gap = np.zeros(int(gap_duration * sample_rate), dtype=np.float32)
        combined = []

        for i, segment in enumerate(processed):
            combined.append(segment)
            if i < len(processed) - 1:  # No gap after last
                combined.append(gap)

        result = np.concatenate(combined)
        log.debug("segments_combined", output_length=len(result))
        return result

    except Exception as e:
        log.error("segment_combination_failed", error=str(e))
        raise AudioProcessingError(f"Failed to combine segments: {e}") from e


def _get_fade_curve(
    samples: int,
    curve: FadeCurve,
    fade_in: bool = True,
) -> NDArray[np.float32]:
    """Generate a fade curve for crossfading.

    Args:
        samples: Number of samples
        curve: Curve type
        fade_in: If True, generate fade-in; else fade-out

    Returns:
        Fade curve array
    """
    t = np.linspace(0, 1, samples)

    if curve == FadeCurve.LINEAR:
        fade = t
    elif curve == FadeCurve.EXPONENTIAL:
        fade = (1 - np.exp(-4 * t)) / (1 - np.exp(-4))
    elif curve == FadeCurve.COSINE:
        fade = (1 - np.cos(np.pi * t)) / 2
    else:  # LOGARITHMIC
        fade = np.log1p(t * (np.e - 1)) / np.log(np.e)

    if not fade_in:
        fade = 1 - fade

    return fade.astype(np.float32)


# =============================================================================
# FILE I/O FUNCTIONS
# =============================================================================


def save_audio(
    audio: NDArray[np.float32],
    output_path: Path | str,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    format: str = "wav",
    subtype: str | None = None,
) -> Path:
    """Save audio to file with format support.

    Args:
        audio: Audio array to save
        output_path: Output file path
        sample_rate: Sample rate in Hz
        format: Audio format (wav, flac, mp3, ogg)
        subtype: Subtype for format (e.g., 'PCM_16', 'PCM_24')

    Returns:
        Path to saved file

    Raises:
        AudioProcessingError: If saving fails
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

        # Determine subtype if not specified
        if subtype is None:
            if format.lower() in ("wav", "flac"):
                subtype = "PCM_16"
            elif format.lower() == "ogg":
                subtype = "VORBIS"

        sf.write(output_path, audio, sample_rate, format=format.upper(), subtype=subtype)

        log.info(
            "audio_saved",
            path=str(output_path),
            size_bytes=output_path.stat().st_size,
        )
        return output_path

    except Exception as e:
        log.error("audio_save_failed", path=str(output_path), error=str(e))
        raise AudioProcessingError(f"Failed to save audio: {e}") from e


def load_audio(
    file_path: Path | str,
    sample_rate: int | None = None,
    mono: bool = True,
) -> tuple[NDArray[np.float32], int]:
    """Load audio from file.

    Args:
        file_path: Path to audio file
        sample_rate: Target sample rate (None = use file's native rate)
        mono: Convert to mono if True

    Returns:
        Tuple of (audio array, sample rate)

    Raises:
        AudioProcessingError: If loading fails
    """
    try:
        file_path = Path(file_path)

        log.debug("loading_audio", path=str(file_path))

        audio, sr = librosa.load(file_path, sr=sample_rate, mono=mono)

        log.debug("audio_loaded", length=len(audio), sample_rate=sr)
        return audio.astype(np.float32), sr

    except Exception as e:
        log.error("audio_load_failed", path=str(file_path), error=str(e))
        raise AudioProcessingError(f"Failed to load audio: {e}") from e


def chunk_audio(
    audio: NDArray[np.float32],
    chunk_size: int = 1024,
    overlap: int = 0,
) -> list[NDArray[np.float32]]:
    """Split audio into chunks for streaming/processing.

    Args:
        audio: Input audio array
        chunk_size: Size of each chunk
        overlap: Overlap between chunks

    Returns:
        List of audio chunks
    """
    chunks = []
    step = chunk_size - overlap

    for i in range(0, len(audio), step):
        chunk = audio[i : i + chunk_size]
        if len(chunk) > 0:
            chunks.append(chunk)

    log.debug(
        "audio_chunked",
        num_chunks=len(chunks),
        chunk_size=chunk_size,
        overlap=overlap,
    )
    return chunks


def get_audio_duration(audio: NDArray[np.float32], sample_rate: int = DEFAULT_SAMPLE_RATE) -> float:
    """Get duration of audio in seconds.

    Args:
        audio: Audio array
        sample_rate: Sample rate in Hz

    Returns:
        Duration in seconds
    """
    return len(audio) / sample_rate


def get_audio_metadata(
    audio: NDArray[np.float32],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> AudioMetadata:
    """Get comprehensive metadata about audio.

    Args:
        audio: Audio array
        sample_rate: Sample rate in Hz

    Returns:
        AudioMetadata object
    """
    duration = len(audio) / sample_rate
    peak = float(np.max(np.abs(audio))) if len(audio) > 0 else 0.0
    rms = float(np.sqrt(np.mean(audio**2))) if len(audio) > 0 else 0.0

    return AudioMetadata(
        duration=duration,
        sample_rate=sample_rate,
        samples=len(audio),
        channels=1,
        peak_amplitude=peak,
        rms_level=rms,
    )


# =============================================================================
# SPEECH-TO-TEXT TRANSCRIPTION
# =============================================================================


def transcribe_audio(
    audio_path: Path | str,
    output_path: Path | str | None = None,
    model_size: str = "medium",
    language: str | None = None,
    task: Literal["transcribe", "translate"] = "transcribe",
    device: str = "auto",
    compute_type: str = "default",
    beam_size: int = 5,
    vad_filter: bool = True,
    word_timestamps: bool = False,
    use_faster_whisper: bool = True,
    initial_prompt: str | None = None,
) -> TranscriptionResult:
    """Transcribe audio file to text using faster-whisper or OpenAI Whisper.

    Uses faster-whisper by default (4x faster than openai-whisper) or falls
    back to OpenAI's Whisper model for speech-to-text transcription.

    faster-whisper advantages:
        - 4x faster than openai-whisper for same accuracy
        - Lower memory usage
        - 8-bit quantization support
        - Built-in VAD filtering
        - Word-level timestamps

    Args:
        audio_path: Path to audio file (wav, mp3, mp4, etc.)
        output_path: Optional path to save transcription as text file
        model_size: Whisper model size:
                   - 'tiny': Fastest, least accurate (~1GB RAM)
                   - 'base': Fast, good accuracy (~1GB RAM)
                   - 'small': Balanced (~2GB RAM)
                   - 'medium': High accuracy (~5GB RAM) [DEFAULT]
                   - 'large', 'large-v2', 'large-v3': Best accuracy (~10GB RAM)
                   - 'turbo', 'large-v3-turbo': Fast with high accuracy (~6GB RAM)
                   - 'distil-large-v3': Compressed (5.8x faster)
        language: Language code (e.g., 'en', 'es', 'hi'). None = auto-detect
        task: 'transcribe' (same language) or 'translate' (to English)
        device: 'cpu', 'cuda', or 'auto'
        compute_type: 'default', 'int8', 'int8_float16', 'float16', 'float32'
        beam_size: Beam size for decoding (5 = default)
        vad_filter: Use Voice Activity Detection to filter silence
        word_timestamps: Return word-level timestamps
        use_faster_whisper: Use faster-whisper if True
        initial_prompt: Text prompt to guide transcription style/script

    Returns:
        TranscriptionResult with text and segments

    Raises:
        AudioProcessingError: If transcription fails
        ImportError: If required package is not installed

    Example:
        >>> result = transcribe_audio("speech.wav")
        >>> print(result.text)

        >>> # Hindi transcription with Devanagari script
        >>> result = transcribe_audio(
        ...     "hindi_speech.wav",
        ...     language="hi",
        ...     initial_prompt="यह एक हिंदी वाक्य है।"
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
            result = _transcribe_faster_whisper(
                audio_path,
                model_size=model_size,
                language=language,
                task=task,
                device=device,
                compute_type=compute_type,
                beam_size=beam_size,
                vad_filter=vad_filter,
                word_timestamps=word_timestamps,
                initial_prompt=initial_prompt,
            )
        else:
            result = _transcribe_openai_whisper(
                audio_path,
                model_size=model_size,
                language=language,
                task=task,
                initial_prompt=initial_prompt,
            )

        # Save to file if output path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.text)

            log.info("transcription_saved", path=str(output_path))

        return result

    except ImportError:
        raise
    except Exception as e:
        log.error("transcription_failed", error=str(e), path=str(audio_path))
        raise AudioProcessingError(f"Failed to transcribe audio: {e}") from e


def _transcribe_faster_whisper(
    audio_path: Path,
    model_size: str,
    language: str | None,
    task: str,
    device: str,
    compute_type: str,
    beam_size: int,
    vad_filter: bool,
    word_timestamps: bool,
    initial_prompt: str | None,
) -> TranscriptionResult:
    """Transcribe using faster-whisper library."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ImportError(
            "faster-whisper is required for fast transcription. "
            "Install with: pip install faster-whisper\n"
            "Or set use_faster_whisper=False to use openai-whisper"
        )

    # Auto-select compute type
    if compute_type == "default":
        if device == "cuda" or (device == "auto" and _is_cuda_available()):
            compute_type = "float16"
        else:
            compute_type = "int8"

    # Auto-select device
    if device == "auto":
        device = "cuda" if _is_cuda_available() else "cpu"

    log.debug(
        "loading_faster_whisper",
        model_size=model_size,
        device=device,
        compute_type=compute_type,
    )

    model = WhisperModel(
        model_size,
        device=device,
        compute_type=compute_type,
        cpu_threads=4,
    )

    # Auto-set Hindi prompt for Devanagari
    if language == "hi" and initial_prompt is None:
        initial_prompt = "यह एक हिंदी वाक्य है। नमस्ते, आप कैसे हैं?"
        log.debug("auto_set_hindi_devanagari_prompt")

    segments_gen, info = model.transcribe(
        str(audio_path),
        language=language,
        task=task,
        beam_size=beam_size,
        vad_filter=vad_filter,
        word_timestamps=word_timestamps,
        initial_prompt=initial_prompt,
    )

    segments_list = list(segments_gen)

    # Format segments
    formatted_segments = []
    for seg in segments_list:
        words = []
        if word_timestamps and hasattr(seg, "words") and seg.words:
            words = [
                {
                    "start": w.start,
                    "end": w.end,
                    "word": w.word,
                    "probability": w.probability,
                }
                for w in seg.words
            ]

        formatted_segments.append(
            TranscriptionSegment(
                id=seg.id,
                start=seg.start,
                end=seg.end,
                text=seg.text,
                words=words,
            )
        )

    text = " ".join([seg.text.strip() for seg in segments_list])

    log.info(
        "transcription_complete",
        text_length=len(text),
        language=info.language,
        probability=f"{info.language_probability:.2%}",
        segments=len(formatted_segments),
    )

    return TranscriptionResult(
        text=text,
        segments=formatted_segments,
        language=info.language,
        language_probability=info.language_probability,
        engine="faster-whisper",
    )


def _transcribe_openai_whisper(
    audio_path: Path,
    model_size: str,
    language: str | None,
    task: str,
    initial_prompt: str | None,
) -> TranscriptionResult:
    """Transcribe using OpenAI Whisper library."""
    try:
        import whisper
    except ImportError:
        raise ImportError(
            "OpenAI Whisper is required. "
            "Install with: pip install openai-whisper\n"
            "Or set use_faster_whisper=True to use faster-whisper (recommended)"
        )

    import sys

    original_stderr = sys.stderr

    try:
        sys.stderr = open(os.devnull, "w")

        log.debug("loading_openai_whisper", model_size=model_size)
        model = whisper.load_model(model_size)

        # Auto-set Hindi prompt
        if language == "hi" and initial_prompt is None:
            initial_prompt = "यह एक हिंदी वाक्य है। नमस्ते, आप कैसे हैं?"

        result = model.transcribe(
            str(audio_path),
            language=language,
            task=task,
            verbose=False,
            initial_prompt=initial_prompt,
        )

    finally:
        sys.stderr.close()
        sys.stderr = original_stderr

    text = result["text"].strip()
    detected_lang = result.get("language", language or "unknown")

    # Format segments
    formatted_segments = []
    for seg in result.get("segments", []):
        formatted_segments.append(
            TranscriptionSegment(
                id=seg.get("id", 0),
                start=seg.get("start", 0),
                end=seg.get("end", 0),
                text=seg.get("text", ""),
            )
        )

    log.info(
        "transcription_complete",
        text_length=len(text),
        language=detected_lang,
        segments=len(formatted_segments),
    )

    return TranscriptionResult(
        text=text,
        segments=formatted_segments,
        language=detected_lang,
        engine="openai-whisper",
    )


def _is_cuda_available() -> bool:
    """Check if CUDA is available for GPU acceleration."""
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


# =============================================================================
# AUDIO ANALYSIS FUNCTIONS
# =============================================================================


def analyze_audio(
    audio: NDArray[np.float32],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> dict:
    """Analyze audio and return comprehensive statistics.

    Args:
        audio: Audio array
        sample_rate: Sample rate in Hz

    Returns:
        Dict with analysis results
    """
    if len(audio) == 0:
        return {"error": "Empty audio"}

    duration = len(audio) / sample_rate
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(audio**2)))
    peak_db = 20 * np.log10(peak) if peak > 0 else -np.inf
    rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf

    # Detect clipping
    clipping_samples = int(np.sum(np.abs(audio) >= 0.999))
    clipping_percentage = (clipping_samples / len(audio)) * 100

    # Estimate dynamic range
    if peak > 0 and rms > 0:
        dynamic_range = peak_db - rms_db
    else:
        dynamic_range = 0

    return {
        "duration_seconds": duration,
        "sample_rate": sample_rate,
        "samples": len(audio),
        "peak_amplitude": peak,
        "peak_db": peak_db,
        "rms_level": rms,
        "rms_db": rms_db,
        "dynamic_range_db": dynamic_range,
        "clipping_samples": clipping_samples,
        "clipping_percentage": clipping_percentage,
        "is_clipping": clipping_percentage > 0.1,
    }


def format_duration(seconds: float) -> str:
    """Format duration as MM:SS.mmm.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string like "02:35.500"

    Example:
        >>> format_duration(125.5)
        '02:05.500'
    """
    if seconds < 0:
        return "00:00.000"

    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:06.3f}"


def detect_silence_regions(
    audio: NDArray[np.float32],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    threshold_db: float = -40.0,
    min_silence_duration: float = 0.1,
) -> list[tuple[float, float]]:
    """Detect regions of silence in audio.

    Args:
        audio: Audio array
        sample_rate: Sample rate in Hz
        threshold_db: Silence threshold in dB
        min_silence_duration: Minimum silence duration (seconds)

    Returns:
        List of (start_time, end_time) tuples for silence regions
    """
    # Convert to dB
    with np.errstate(divide="ignore"):
        db = 20 * np.log10(np.abs(audio) + 1e-10)

    # Find silence mask
    silence_mask = db < threshold_db

    # Find contiguous regions
    regions = []
    in_silence = False
    silence_start = 0

    min_samples = int(min_silence_duration * sample_rate)

    for i, is_silent in enumerate(silence_mask):
        if is_silent and not in_silence:
            in_silence = True
            silence_start = i
        elif not is_silent and in_silence:
            in_silence = False
            if i - silence_start >= min_samples:
                regions.append((silence_start / sample_rate, i / sample_rate))

    # Handle case where audio ends in silence
    if in_silence and len(audio) - silence_start >= min_samples:
        regions.append((silence_start / sample_rate, len(audio) / sample_rate))

    return regions
