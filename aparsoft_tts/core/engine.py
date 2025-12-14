# aparsoft_tts/core/engine.py

"""World-Class TTS Engine using Kokoro TTS v0.9.4+ with Advanced Features.

This module provides a production-grade TTSEngine class that interfaces with the
Kokoro TTS model. Built on latest best practices from Kokoro, Kokoro-FastAPI,
and modern Python async/concurrent patterns.

Key Features:
- 🎯 Intelligent token-aware chunking (100-250 optimal, 450 max)
- 🔀 Voice mixing support (e.g., 'af_sky+af_bella' for blended voices)
- 🚀 Async generation with asyncio.to_thread for non-blocking I/O
- ⚡ Concurrent batch processing with ThreadPoolExecutor
- 📊 Phoneme and timestamp generation for captions/subtitles
- 🌍 Multi-language support (9 languages: a, b, e, f, h, i, j, p, z)
- 🎨 Voice-specific audio enhancement profiles
- 📝 Natural boundary detection for text splitting
- 💾 Pipeline caching for performance
- 🔧 MPS GPU acceleration support (macOS)

Kokoro Model Architecture:
    - 82M parameters, StyleTTS 2 architecture
    - 24kHz sample rate, high-quality neural vocoder
    - Maximum: 510 tokens per pass (architectural limit)
    - Optimal: 100-250 tokens per chunk (best quality)
    - Rushed speech warning: >400 tokens

References:
    - https://github.com/hexgrad/kokoro (v0.9.4+)
    - https://huggingface.co/hexgrad/Kokoro-82M
    - https://github.com/remsky/Kokoro-FastAPI
"""

from __future__ import annotations

import asyncio
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Literal, NamedTuple

import numpy as np
from numpy.typing import NDArray

from aparsoft_tts.config import TTSConfig, get_config
from aparsoft_tts.utils.audio import (
    combine_audio_segments,
    enhance_audio,
    get_audio_duration,
    save_audio,
)
from aparsoft_tts.utils.exceptions import (
    InvalidParameterError,
    InvalidVoiceError,
    ModelLoadError,
    TTSGenerationError,
)
from aparsoft_tts.utils.logging import LoggerMixin

if TYPE_CHECKING:
    from kokoro import KPipeline

# =============================================================================
# CONSTANTS AND VOICE DEFINITIONS
# =============================================================================

# Enable MPS fallback for macOS GPU acceleration
# Reference: https://github.com/hexgrad/kokoro#gpu-acceleration
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

# Default split pattern for text chunking (from kokoro v0.9.4+)
DEFAULT_SPLIT_PATTERN = r"\n+"


# Voice Categories with Metadata
@dataclass(frozen=True, slots=True)
class VoiceInfo:
    """Metadata for a voice."""

    name: str
    lang_code: str
    gender: Literal["male", "female"]
    accent: str
    description: str


# English American Voices
AMERICAN_MALE_VOICES = [
    VoiceInfo("am_adam", "a", "male", "american", "Natural inflection, conversational"),
    VoiceInfo("am_michael", "a", "male", "american", "Deeper tones, professional"),
]

AMERICAN_FEMALE_VOICES = [
    VoiceInfo("af_bella", "a", "female", "american", "Warm tones, friendly"),
    VoiceInfo("af_nicole", "a", "female", "american", "Dynamic range, expressive"),
    VoiceInfo("af_sarah", "a", "female", "american", "Clear articulation, soft attack"),
    VoiceInfo("af_sky", "a", "female", "american", "Youthful energy, bright"),
]

# English British Voices
BRITISH_MALE_VOICES = [
    VoiceInfo("bm_george", "b", "male", "british", "Classic accent, authoritative"),
    VoiceInfo("bm_lewis", "b", "male", "british", "Modern accent, casual"),
]

BRITISH_FEMALE_VOICES = [
    VoiceInfo("bf_emma", "b", "female", "british", "Professional, clear"),
    VoiceInfo("bf_isabella", "b", "female", "british", "Soft tones, gentle"),
]

# Special/Mixed Voices
SPECIAL_VOICES = [
    VoiceInfo("af", "a", "female", "american", "Default voice (Bella + Sarah mix)"),
]

# Hindi Voices (requires espeak-ng with Hindi support)
HINDI_MALE_VOICES = [
    VoiceInfo("hm_omega", "h", "male", "hindi", "Hindi male - omega"),
    VoiceInfo("hm_psi", "h", "male", "hindi", "Hindi male - psi"),
]

HINDI_FEMALE_VOICES = [
    VoiceInfo("hf_alpha", "h", "female", "hindi", "Hindi female - alpha"),
    VoiceInfo("hf_beta", "h", "female", "hindi", "Hindi female - beta"),
]

# Aggregate voice lists
MALE_VOICES = [v.name for v in AMERICAN_MALE_VOICES + BRITISH_MALE_VOICES]
FEMALE_VOICES = [v.name for v in AMERICAN_FEMALE_VOICES + BRITISH_FEMALE_VOICES + SPECIAL_VOICES]
HINDI_MALE_VOICE_NAMES = [v.name for v in HINDI_MALE_VOICES]
HINDI_FEMALE_VOICE_NAMES = [v.name for v in HINDI_FEMALE_VOICES]

ALL_VOICE_INFO = (
    AMERICAN_MALE_VOICES
    + AMERICAN_FEMALE_VOICES
    + BRITISH_MALE_VOICES
    + BRITISH_FEMALE_VOICES
    + SPECIAL_VOICES
    + HINDI_MALE_VOICES
    + HINDI_FEMALE_VOICES
)

ALL_VOICES = [v.name for v in ALL_VOICE_INFO]
VOICE_REGISTRY = {v.name: v for v in ALL_VOICE_INFO}

# Language code mappings (Kokoro v0.9.4+ standard)
LANG_CODE_MAP = {
    # Prefix -> Lang Code
    "am_": "a",  # American English
    "af_": "a",  # American English (female)
    "af": "a",  # Special voice (no underscore)
    "bm_": "b",  # British English
    "bf_": "b",  # British English (female)
    "hm_": "h",  # Hindi
    "hf_": "h",  # Hindi (female)
    "jm_": "j",  # Japanese
    "jf_": "j",  # Japanese (female)
    "zm_": "z",  # Mandarin Chinese
    "zf_": "z",  # Mandarin Chinese (female)
    "em_": "e",  # Spanish
    "ef_": "e",  # Spanish (female)
    "im_": "i",  # Italian
    "if_": "i",  # Italian (female)
    "pm_": "p",  # Brazilian Portuguese
    "pf_": "p",  # Brazilian Portuguese (female)
    "fm_": "f",  # French
    "ff_": "f",  # French (female)
}

# Supported language codes
SUPPORTED_LANG_CODES = frozenset("abefhijpz")


# =============================================================================
# DATA CLASSES FOR STRUCTURED OUTPUTS
# =============================================================================


class TimestampedWord(NamedTuple):
    """Word with timing information for captions."""

    word: str
    start: float
    end: float
    phonemes: str = ""


@dataclass
class GenerationResult:
    """Result from TTS generation with metadata."""

    audio: NDArray[np.float32]
    sample_rate: int
    duration: float
    voice: str
    text: str
    tokens: int
    phonemes: str = ""
    timestamps: list[TimestampedWord] = field(default_factory=list)

    @property
    def duration_formatted(self) -> str:
        """Duration as MM:SS.mmm format."""
        mins = int(self.duration // 60)
        secs = self.duration % 60
        return f"{mins:02d}:{secs:06.3f}"


@dataclass
class ChunkInfo:
    """Information about a text chunk for processing."""

    text: str
    tokens: int
    index: int
    total: int

    @property
    def progress(self) -> float:
        """Progress as percentage (0-100)."""
        return (self.index / self.total) * 100 if self.total > 0 else 0


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_lang_code_from_voice(voice: str) -> str:
    """Get the correct lang_code for a voice based on its prefix.

    Kokoro requires lang_code to match voice prefix for proper phonemization.

    Supported Languages:
        - 'a': American English (am_*, af_*)
        - 'b': British English (bm_*, bf_*)
        - 'h': Hindi (hm_*, hf_*)
        - 'j': Japanese (jm_*, jf_*)
        - 'z': Mandarin Chinese (zm_*, zf_*)
        - 'e': Spanish (em_*, ef_*)
        - 'i': Italian (im_*, if_*)
        - 'p': Brazilian Portuguese (pm_*, pf_*)
        - 'f': French (fm_*, ff_*)

    Args:
        voice: Voice name (e.g., 'am_michael', 'hf_alpha', 'bm_george')
               Can also be a mixed voice like 'af_sky+af_bella'

    Returns:
        Lang code character

    Example:
        >>> get_lang_code_from_voice('am_michael')
        'a'
        >>> get_lang_code_from_voice('hf_alpha')
        'h'
        >>> get_lang_code_from_voice('af_sky+af_bella')
        'a'
    """
    # Handle mixed voices - use first voice's lang_code
    if "+" in voice:
        voice = voice.split("+")[0].strip()

    # Check prefix mappings
    for prefix, lang_code in LANG_CODE_MAP.items():
        if voice.startswith(prefix):
            return lang_code

    # Fallback: use first character if valid
    if voice and voice[0] in SUPPORTED_LANG_CODES:
        return voice[0]

    # Default to American English
    return "a"


def parse_mixed_voice(voice_spec: str) -> list[tuple[str, float]]:
    """Parse a voice specification that may include mixing.

    Supports Kokoro-FastAPI style voice mixing:
        - 'af_sky': Single voice (weight 1.0)
        - 'af_sky+af_bella': Equal mix (0.5 each)
        - 'af_sky*0.7+af_bella*0.3': Weighted mix

    Args:
        voice_spec: Voice specification string

    Returns:
        List of (voice_name, weight) tuples

    Example:
        >>> parse_mixed_voice('af_sky')
        [('af_sky', 1.0)]
        >>> parse_mixed_voice('af_sky+af_bella')
        [('af_sky', 0.5), ('af_bella', 0.5)]
        >>> parse_mixed_voice('af_sky*0.7+af_bella*0.3')
        [('af_sky', 0.7), ('af_bella', 0.3)]
    """
    parts = voice_spec.split("+")
    voices = []

    for part in parts:
        part = part.strip()
        if "*" in part:
            # Weighted voice: 'voice*weight'
            name, weight_str = part.split("*", 1)
            weight = float(weight_str)
        else:
            # Unweighted voice
            name = part
            weight = None
        voices.append((name.strip(), weight))

    # If no weights specified, distribute equally
    if all(w is None for _, w in voices):
        equal_weight = 1.0 / len(voices)
        voices = [(name, equal_weight) for name, _ in voices]
    else:
        # Fill in missing weights
        voices = [(name, w if w is not None else 0.0) for name, w in voices]

    return voices


def validate_voice(voice: str) -> None:
    """Validate a voice specification.

    Args:
        voice: Voice name or mixed voice specification

    Raises:
        InvalidVoiceError: If voice is invalid
    """
    voices = parse_mixed_voice(voice)

    for voice_name, weight in voices:
        if voice_name not in ALL_VOICES:
            raise InvalidVoiceError(
                f"Invalid voice: '{voice_name}'. " f"Available voices: {', '.join(ALL_VOICES)}"
            )
        if weight < 0 or weight > 1:
            raise InvalidVoiceError(f"Voice weight must be between 0 and 1, got {weight}")


# =============================================================================
# MAIN TTS ENGINE CLASS
# =============================================================================


class TTSEngine(LoggerMixin):
    """World-class TTS engine with advanced features and best practices.

    This class provides a production-grade interface to the Kokoro TTS model with:
    - 🎯 Intelligent token-aware chunking for optimal audio quality
    - 🔀 Voice mixing support for blended voice characteristics
    - 🚀 Async/concurrent processing for performance
    - 📊 Phoneme and timestamp generation for subtitles
    - 🌍 Multi-language support (9 languages)
    - 🎨 Voice-specific audio enhancement

    Token Limits (Kokoro Architecture):
        - Maximum: 510 tokens per pass (hard architectural limit)
        - Optimal: 100-250 tokens (best audio quality)
        - Warning: >400 tokens may cause rushed speech
        - Configurable via TTSConfig

    Voice Mixing:
        Supports Kokoro-FastAPI style voice combinations:
        - 'af_sky+af_bella': Equal 50/50 mix
        - 'af_sky*0.7+af_bella*0.3': Weighted 70/30 mix

    Async Support:
        - generate_async(): Non-blocking async generation
        - batch_generate_async(): Concurrent batch processing
        - Uses asyncio.to_thread for I/O operations

    Example:
        >>> # Basic usage
        >>> engine = TTSEngine()
        >>> engine.generate("Hello world", "output.wav")

        >>> # Voice mixing
        >>> engine.generate("Hello", "output.wav", voice="af_sky+af_bella")

        >>> # Async batch processing
        >>> async def main():
        ...     engine = TTSEngine()
        ...     paths = await engine.batch_generate_async(
        ...         ["Text 1", "Text 2", "Text 3"],
        ...         "outputs/"
        ...     )

        >>> # With timestamps for subtitles
        >>> result = engine.generate_with_metadata("Hello world")
        >>> for word in result.timestamps:
        ...     print(f"[{word.start:.2f}s] {word.word}")
    """

    # Class-level executor for async operations
    _executor: ThreadPoolExecutor | None = None
    _executor_max_workers: int = 4

    def __init__(
        self,
        config: TTSConfig | None = None,
        *,
        lazy_init: bool = False,
        max_workers: int | None = None,
    ):
        """Initialize TTS engine.

        Args:
            config: TTS configuration. If None, uses default config.
            lazy_init: If True, delay pipeline initialization until first use.
            max_workers: Max workers for concurrent operations. Default: 4.

        Raises:
            ModelLoadError: If model fails to load (when lazy_init=False)
        """
        self.config = config or get_config().tts

        # Pipeline cache: lang_code -> KPipeline
        self._pipelines: dict[str, KPipeline] = {}
        self._pipeline_lock = asyncio.Lock()
        self.repo_id = self.config.repo_id

        # Configure thread pool executor
        if max_workers:
            TTSEngine._executor_max_workers = max_workers

        self.log.info(
            "initializing_tts_engine",
            voice=self.config.voice,
            token_limits=f"{self.config.token_target_min}-{self.config.token_target_max}",
            lazy_init=lazy_init,
        )

        if not lazy_init:
            try:
                # Pre-initialize pipeline for default voice
                default_lang = get_lang_code_from_voice(self.config.voice)
                self._get_pipeline(default_lang)
                self.log.info("tts_engine_initialized", default_lang_code=default_lang)
            except Exception as e:
                self.log.error("tts_initialization_failed", error=str(e))
                raise ModelLoadError(f"Failed to initialize TTS model: {e}") from e

    @classmethod
    def get_executor(cls) -> ThreadPoolExecutor:
        """Get or create the shared thread pool executor."""
        if cls._executor is None:
            cls._executor = ThreadPoolExecutor(
                max_workers=cls._executor_max_workers,
                thread_name_prefix="tts_worker",
            )
        return cls._executor

    @classmethod
    def shutdown_executor(cls, wait: bool = True) -> None:
        """Shutdown the shared executor."""
        if cls._executor is not None:
            cls._executor.shutdown(wait=wait)
            cls._executor = None

    def _get_pipeline(self, lang_code: str) -> "KPipeline":
        """Get or create a KPipeline for the specified lang_code.

        Pipelines are cached to avoid recreation overhead. Thread-safe.

        Args:
            lang_code: Language code ('a', 'b', 'h', etc.)

        Returns:
            KPipeline instance for the lang_code
        """
        if lang_code not in self._pipelines:
            self.log.debug("creating_pipeline", lang_code=lang_code, repo_id=self.repo_id)
            from kokoro import KPipeline

            self._pipelines[lang_code] = KPipeline(
                lang_code=lang_code,
                repo_id=self.repo_id,
            )
        return self._pipelines[lang_code]

    async def _get_pipeline_async(self, lang_code: str) -> "KPipeline":
        """Async version of _get_pipeline with lock for thread safety."""
        async with self._pipeline_lock:
            if lang_code not in self._pipelines:
                # Run pipeline creation in thread pool
                pipeline = await asyncio.to_thread(self._create_pipeline, lang_code)
                self._pipelines[lang_code] = pipeline
            return self._pipelines[lang_code]

    def _create_pipeline(self, lang_code: str) -> "KPipeline":
        """Create a new pipeline (called from thread pool)."""
        from kokoro import KPipeline

        self.log.debug("creating_pipeline_async", lang_code=lang_code)
        return KPipeline(lang_code=lang_code, repo_id=self.repo_id)

    # =========================================================================
    # TOKEN COUNTING AND TEXT CHUNKING
    # =========================================================================

    def _count_tokens(self, text: str, lang_code: str = "a") -> int:
        """Count phonemized tokens for text using Kokoro's G2P.

        Uses the pipeline's grapheme-to-phoneme converter for accurate
        token counting. This is critical for preventing rushed speech.

        Args:
            text: Input text
            lang_code: Language code for phonemization

        Returns:
            Number of phonemized tokens

        Note:
            Falls back to character-based estimate if G2P fails.
        """
        try:
            pipeline = self._get_pipeline(lang_code)

            # Use pipeline's G2P (misaki library under the hood)
            if lang_code in "ab":
                # English: g2p returns (phonemes, tokens)
                ps, tokens = pipeline.g2p(text)
                return len(ps) if ps else 0
            else:
                # Other languages: g2p returns (phonemes, _)
                ps, _ = pipeline.g2p(text)
                return len(ps) if ps else 0

        except Exception as e:
            # Fallback: ~4 chars per token for English
            self.log.warning("token_count_fallback", error=str(e))
            return max(1, len(text) // 4)

    def _get_phonemes(self, text: str, lang_code: str = "a") -> str:
        """Get phoneme representation of text.

        Useful for debugging pronunciation issues or generating
        phoneme-level captions.

        Args:
            text: Input text
            lang_code: Language code

        Returns:
            Phoneme string
        """
        try:
            pipeline = self._get_pipeline(lang_code)

            if lang_code in "ab":
                ps, _ = pipeline.g2p(text)
            else:
                ps, _ = pipeline.g2p(text)

            return ps if ps else ""

        except Exception as e:
            self.log.warning("phoneme_extraction_failed", error=str(e))
            return ""

    def _chunk_text_smart(
        self,
        text: str,
        target_min_tokens: int | None = None,
        target_max_tokens: int | None = None,
        absolute_max_tokens: int | None = None,
        lang_code: str = "a",
    ) -> list[ChunkInfo]:
        """Chunk text intelligently based on token limits and natural boundaries.

        Implements best practices for Kokoro TTS:
        - Optimal range: 100-250 tokens per chunk (configurable)
        - Never exceed hard limit (prevents rushed speech)
        - Split at sentence boundaries when possible
        - Uses Kokoro's native split_pattern for preprocessing
        - Avoid very short chunks (<20 tokens)
        - Handle edge cases (oversized sentences, etc.)

        Algorithm:
            1. Pre-split by newlines (Kokoro native pattern)
            2. Split remaining by sentences
            3. Combine sentences until target_max_tokens
            4. For oversized sentences, split by clauses (commas/semicolons)
            5. Last resort: force split by words
            6. Merge very short final chunks with previous

        Args:
            text: Input text to chunk
            target_min_tokens: Minimum tokens per chunk
            target_max_tokens: Target maximum tokens per chunk
            absolute_max_tokens: Hard limit (prevents rushed speech)
            lang_code: Language code for token counting

        Returns:
            List of ChunkInfo objects with text and metadata

        Example:
            >>> engine = TTSEngine()
            >>> chunks = engine._chunk_text_smart("Long text here...")
            >>> for chunk in chunks:
            ...     print(f"Chunk {chunk.index}: {chunk.tokens} tokens")
        """
        # Use config values if not provided
        target_min = target_min_tokens or self.config.token_target_min
        target_max = target_max_tokens or self.config.token_target_max
        absolute_max = absolute_max_tokens or self.config.token_absolute_max

        # Pre-process: split by newlines (Kokoro native pattern)
        paragraphs = re.split(DEFAULT_SPLIT_PATTERN, text)

        # Split into sentences
        sentences = []
        for para in paragraphs:
            para = para.strip()
            if para:
                # Split by sentence-ending punctuation
                para_sentences = re.split(r"(?<=[.!?])\s+", para)
                sentences.extend(s.strip() for s in para_sentences if s.strip())

        chunks: list[str] = []
        current_chunk: list[str] = []
        current_tokens = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_tokens = self._count_tokens(sentence, lang_code)

            # Handle oversized single sentences
            if sentence_tokens > absolute_max:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                # Split by clauses (commas, semicolons, colons)
                parts = re.split(r"[,;:]\s+", sentence)
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue

                    part_tokens = self._count_tokens(part, lang_code)

                    if part_tokens > absolute_max:
                        # Force split by words as last resort
                        words = part.split()
                        for word in words:
                            word_tokens = self._count_tokens(word, lang_code)
                            if current_tokens + word_tokens <= target_max:
                                current_chunk.append(word)
                                current_tokens += word_tokens
                            else:
                                if current_chunk:
                                    chunks.append(" ".join(current_chunk))
                                current_chunk = [word]
                                current_tokens = word_tokens
                    else:
                        if current_tokens + part_tokens <= target_max:
                            current_chunk.append(part)
                            current_tokens += part_tokens
                        else:
                            if current_chunk:
                                chunks.append(" ".join(current_chunk))
                            current_chunk = [part]
                            current_tokens = part_tokens
                continue

            # Normal sentence handling
            if current_tokens + sentence_tokens <= target_max:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
            else:
                # Start new chunk
                if current_chunk:
                    if current_tokens >= target_min or not chunks:
                        chunks.append(" ".join(current_chunk))
                    elif chunks:
                        # Chunk too small, merge with previous
                        chunks[-1] += " " + " ".join(current_chunk)

                current_chunk = [sentence]
                current_tokens = sentence_tokens

        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if current_tokens >= 20 or not chunks:
                chunks.append(chunk_text)
            elif chunks:
                chunks[-1] += " " + chunk_text

        # Convert to ChunkInfo objects with metadata
        total_chunks = len(chunks)
        return [
            ChunkInfo(
                text=chunk,
                tokens=self._count_tokens(chunk, lang_code),
                index=i + 1,
                total=total_chunks,
            )
            for i, chunk in enumerate(chunks)
        ]

    # =========================================================================
    # CORE GENERATION METHODS
    # =========================================================================

    def _generate_chunk(
        self,
        text: str,
        voice: str,
        speed: float,
        lang_code: str,
    ) -> NDArray[np.float32]:
        """Generate audio for a single text chunk.

        Internal method used by generate() and other methods.

        Args:
            text: Text to convert
            voice: Voice name
            speed: Speech speed
            lang_code: Language code

        Returns:
            Audio array (float32, 24kHz)
        """
        pipeline = self._get_pipeline(lang_code)

        # Use Kokoro's generator pattern: (graphemes, phonemes, audio)
        generator = pipeline(text, voice=voice, speed=speed)

        audio_chunks = []
        for _, _, audio in generator:
            # Handle torch tensors if returned
            if hasattr(audio, "cpu"):
                audio = audio.cpu().numpy()
            audio_chunks.append(audio)

        return np.concatenate(audio_chunks).astype(np.float32)

    def generate(
        self,
        text: str,
        output_path: Path | str | None = None,
        voice: str | None = None,
        speed: float | None = None,
        enhance: bool | None = None,
    ) -> Path | NDArray[np.float32]:
        """Generate speech from text with automatic intelligent chunking.

        For texts exceeding token_target_max, automatically chunks at
        natural boundaries to maintain optimal audio quality and prevent
        rushed speech artifacts.

        Args:
            text: Input text to convert to speech
            output_path: Output file path. If None, returns audio array.
            voice: Voice to use (overrides config). Supports mixing:
                   - 'af_sarah': Single voice
                   - 'af_sky+af_bella': Equal mix
                   - 'af_sky*0.7+af_bella*0.3': Weighted mix
            speed: Speech speed (0.5-2.0, overrides config)
            enhance: Apply audio enhancement (overrides config)

        Returns:
            Path to saved file if output_path provided, else audio array

        Raises:
            TTSGenerationError: If generation fails
            InvalidVoiceError: If voice is invalid
            InvalidParameterError: If parameters are invalid

        Example:
            >>> engine = TTSEngine()
            >>> # Basic generation
            >>> path = engine.generate("Hello", "output.wav")

            >>> # Get audio array directly
            >>> audio = engine.generate("Hello")

            >>> # Voice mixing
            >>> audio = engine.generate("Hello", voice="af_sky+af_bella")

            >>> # Long text (auto-chunked for quality)
            >>> engine.generate("..." * 500, "long.wav")
        """
        # Validate and resolve parameters
        voice = voice or self.config.voice
        validate_voice(voice)

        speed = speed if speed is not None else self.config.speed
        if not 0.5 <= speed <= 2.0:
            raise InvalidParameterError(f"Speed must be between 0.5 and 2.0, got {speed}")

        enhance = enhance if enhance is not None else self.config.enhance_audio

        try:
            # Get language code from first voice in mix
            voice_lang_code = get_lang_code_from_voice(voice)
            token_count = self._count_tokens(text, voice_lang_code)

            self.log.info(
                "generating_speech",
                text_length=len(text),
                tokens=token_count,
                voice=voice,
                speed=speed,
                enhance=enhance,
            )

            # Chunk if needed for optimal quality
            if token_count > self.config.token_target_max:
                self.log.info(
                    "chunking_text",
                    tokens=token_count,
                    target_max=self.config.token_target_max,
                )

                chunks = self._chunk_text_smart(text, lang_code=voice_lang_code)
                audio_chunks = []

                for chunk_info in chunks:
                    self.log.debug(
                        "processing_chunk",
                        chunk_num=chunk_info.index,
                        total=chunk_info.total,
                        tokens=chunk_info.tokens,
                        preview=chunk_info.text[:50],
                    )

                    chunk_audio = self._generate_chunk(
                        chunk_info.text, voice, speed, voice_lang_code
                    )
                    audio_chunks.append(chunk_audio)

                # Combine chunks with configured gap
                final_audio = combine_audio_segments(
                    audio_chunks,
                    sample_rate=self.config.sample_rate,
                    gap_duration=self.config.chunk_gap_duration,
                )

                self.log.info("chunks_combined", num_chunks=len(chunks))
            else:
                # Direct generation for short text
                final_audio = self._generate_chunk(text, voice, speed, voice_lang_code)

            # Apply audio enhancement if requested
            if enhance:
                final_audio = enhance_audio(
                    final_audio,
                    sample_rate=self.config.sample_rate,
                    trim_silence=self.config.trim_silence,
                    trim_db=self.config.trim_db,
                    fade_duration=self.config.fade_duration,
                    voice_name=voice,
                )

            duration = get_audio_duration(final_audio, self.config.sample_rate)
            self.log.info(
                "speech_generated",
                duration=f"{duration:.2f}s",
                samples=len(final_audio),
            )

            # Save or return
            if output_path:
                return save_audio(
                    final_audio,
                    output_path,
                    sample_rate=self.config.sample_rate,
                    format=self.config.output_format,
                )
            return final_audio

        except (InvalidVoiceError, InvalidParameterError):
            raise
        except Exception as e:
            self.log.error("speech_generation_failed", error=str(e))
            raise TTSGenerationError(f"Failed to generate speech: {e}") from e

    def generate_with_metadata(
        self,
        text: str,
        voice: str | None = None,
        speed: float | None = None,
        enhance: bool | None = None,
        include_timestamps: bool = True,
    ) -> GenerationResult:
        """Generate speech with full metadata including timestamps.

        Useful for creating captions, subtitles, or analyzing speech output.

        Args:
            text: Input text
            voice: Voice to use
            speed: Speech speed
            enhance: Apply enhancement
            include_timestamps: Include word-level timestamps

        Returns:
            GenerationResult with audio and metadata

        Example:
            >>> result = engine.generate_with_metadata("Hello world")
            >>> print(f"Duration: {result.duration_formatted}")
            >>> for word in result.timestamps:
            ...     print(f"[{word.start:.2f}s] {word.word}")
        """
        voice = voice or self.config.voice
        validate_voice(voice)
        speed = speed if speed is not None else self.config.speed
        enhance = enhance if enhance is not None else self.config.enhance_audio

        voice_lang_code = get_lang_code_from_voice(voice)
        tokens = self._count_tokens(text, voice_lang_code)
        phonemes = self._get_phonemes(text, voice_lang_code)

        # Generate audio
        audio = self.generate(text, voice=voice, speed=speed, enhance=enhance)
        if isinstance(audio, Path):
            raise TTSGenerationError("Unexpected path return")

        duration = get_audio_duration(audio, self.config.sample_rate)

        # Generate timestamps if requested
        timestamps = []
        if include_timestamps:
            # Estimate word timings based on phoneme distribution
            words = text.split()
            if words:
                # Simple linear distribution (more sophisticated timing would
                # require analyzing the actual audio or using forced alignment)
                time_per_word = duration / len(words)
                for i, word in enumerate(words):
                    timestamps.append(
                        TimestampedWord(
                            word=word,
                            start=i * time_per_word,
                            end=(i + 1) * time_per_word,
                        )
                    )

        return GenerationResult(
            audio=audio,
            sample_rate=self.config.sample_rate,
            duration=duration,
            voice=voice,
            text=text,
            tokens=tokens,
            phonemes=phonemes,
            timestamps=timestamps,
        )

    def generate_stream(
        self,
        text: str,
        voice: str | None = None,
        speed: float | None = None,
    ) -> Iterator[NDArray[np.float32]]:
        """Generate speech as a stream of audio chunks.

        Useful for real-time applications, streaming to clients, or
        processing long texts with low latency.

        Args:
            text: Input text
            voice: Voice to use
            speed: Speech speed

        Yields:
            Audio chunks as they're generated

        Raises:
            TTSGenerationError: If generation fails

        Example:
            >>> for chunk in engine.generate_stream("Long text..."):
            ...     stream_to_client(chunk)
        """
        voice = voice or self.config.voice
        speed = speed if speed is not None else self.config.speed

        try:
            voice_lang_code = get_lang_code_from_voice(voice)
            pipeline = self._get_pipeline(voice_lang_code)

            token_count = self._count_tokens(text, voice_lang_code)
            self.log.info(
                "generating_stream",
                tokens=token_count,
                voice=voice,
            )

            # Chunk if needed
            if token_count > self.config.token_target_max:
                chunks = self._chunk_text_smart(text, lang_code=voice_lang_code)
                for chunk_info in chunks:
                    generator = pipeline(chunk_info.text, voice=voice, speed=speed)
                    for _, _, audio in generator:
                        if hasattr(audio, "cpu"):
                            audio = audio.cpu().numpy()
                        yield audio.astype(np.float32)
            else:
                generator = pipeline(text, voice=voice, speed=speed)
                for _, _, audio in generator:
                    if hasattr(audio, "cpu"):
                        audio = audio.cpu().numpy()
                    yield audio.astype(np.float32)

        except Exception as e:
            self.log.error("stream_generation_failed", error=str(e))
            raise TTSGenerationError(f"Failed to generate stream: {e}") from e

    # =========================================================================
    # ASYNC METHODS
    # =========================================================================

    async def generate_async(
        self,
        text: str,
        output_path: Path | str | None = None,
        voice: str | None = None,
        speed: float | None = None,
        enhance: bool | None = None,
    ) -> Path | NDArray[np.float32]:
        """Async version of generate() for non-blocking I/O.

        Uses asyncio.to_thread to run generation in a thread pool,
        preventing blocking of the event loop.

        Args:
            text: Input text
            output_path: Output file path (optional)
            voice: Voice to use
            speed: Speech speed
            enhance: Apply enhancement

        Returns:
            Path or audio array

        Example:
            >>> async def main():
            ...     engine = TTSEngine()
            ...     audio = await engine.generate_async("Hello")
        """
        return await asyncio.to_thread(
            self.generate,
            text,
            output_path,
            voice,
            speed,
            enhance,
        )

    async def batch_generate_async(
        self,
        texts: list[str],
        output_dir: Path | str,
        voice: str | None = None,
        speed: float | None = None,
        filename_prefix: str = "audio",
        max_concurrent: int | None = None,
    ) -> list[Path]:
        """Generate multiple audio files concurrently.

        Uses asyncio.gather for concurrent generation, significantly
        faster than sequential processing for multiple texts.

        Args:
            texts: List of texts to convert
            output_dir: Output directory
            voice: Voice to use
            speed: Speech speed
            filename_prefix: Prefix for filenames
            max_concurrent: Max concurrent tasks (default: all at once)

        Returns:
            List of paths to generated files

        Example:
            >>> async def main():
            ...     paths = await engine.batch_generate_async(
            ...         ["Text 1", "Text 2"],
            ...         "outputs/"
            ...     )
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        self.log.info(
            "batch_generation_started",
            num_texts=len(texts),
            output_dir=str(output_dir),
        )

        # Create tasks for each text
        async def generate_one(i: int, text: str) -> Path:
            output_file = output_dir / f"{filename_prefix}_{i:03d}.{self.config.output_format}"
            result = await self.generate_async(text, output_file, voice, speed)
            if isinstance(result, Path):
                return result
            raise TTSGenerationError("Expected path return")

        # Run with optional concurrency limit
        if max_concurrent:
            semaphore = asyncio.Semaphore(max_concurrent)

            async def limited_generate(i: int, text: str) -> Path:
                async with semaphore:
                    return await generate_one(i, text)

            paths = await asyncio.gather(
                *[limited_generate(i, text) for i, text in enumerate(texts, 1)]
            )
        else:
            paths = await asyncio.gather(
                *[generate_one(i, text) for i, text in enumerate(texts, 1)]
            )

        self.log.info("batch_generation_completed", num_files=len(paths))
        return list(paths)

    # =========================================================================
    # BATCH AND SCRIPT PROCESSING
    # =========================================================================

    def batch_generate(
        self,
        texts: list[str],
        output_dir: Path | str,
        voice: str | None = None,
        speed: float | None = None,
        filename_prefix: str = "audio",
        max_workers: int | None = None,
    ) -> list[Path]:
        """Generate multiple audio files with concurrent processing.

        Uses ThreadPoolExecutor for parallel generation, significantly
        faster than sequential processing.

        Args:
            texts: List of texts to convert
            output_dir: Output directory
            voice: Voice to use
            speed: Speech speed
            filename_prefix: Prefix for filenames
            max_workers: Max worker threads (default: 4)

        Returns:
            List of paths to generated files

        Example:
            >>> paths = engine.batch_generate(
            ...     ["Intro", "Body", "Outro"],
            ...     "outputs/"
            ... )
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        self.log.info(
            "batch_generation_started",
            num_texts=len(texts),
            output_dir=str(output_dir),
        )

        def generate_one(args: tuple[int, str]) -> Path:
            i, text = args
            output_file = output_dir / f"{filename_prefix}_{i:03d}.{self.config.output_format}"
            result = self.generate(text, output_file, voice=voice, speed=speed)
            if isinstance(result, Path):
                return result
            raise TTSGenerationError("Expected path return")

        # Use thread pool for concurrent generation
        workers = max_workers or self._executor_max_workers
        paths = []

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(generate_one, (i, text)): i for i, text in enumerate(texts, 1)
            }

            for future in as_completed(futures):
                i = futures[future]
                try:
                    path = future.result()
                    paths.append((i, path))
                    self.log.info("batch_item_generated", index=i, path=str(path))
                except Exception as e:
                    self.log.error("batch_item_failed", index=i, error=str(e))
                    raise

        # Sort by index to maintain order
        paths.sort(key=lambda x: x[0])
        result_paths = [p for _, p in paths]

        self.log.info("batch_generation_completed", num_files=len(result_paths))
        return result_paths

    def process_script(
        self,
        script_path: Path | str,
        output_path: Path | str,
        gap_duration: float = 0.5,
        voice: str | None = None,
        speed: float | None = None,
    ) -> Path:
        """Process a complete script file with intelligent chunking.

        Reads script, applies token-aware chunking for optimal quality,
        generates audio for each chunk, and combines with gaps.

        Args:
            script_path: Path to script text file
            output_path: Output audio file path
            gap_duration: Gap between segments (seconds)
            voice: Voice to use
            speed: Speech speed

        Returns:
            Path to output file

        Raises:
            TTSGenerationError: If processing fails
            FileNotFoundError: If script file not found

        Example:
            >>> engine.process_script("script.txt", "voiceover.wav")
        """
        script_path = Path(script_path)

        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")

        self.log.info("processing_script", path=str(script_path))

        # Read script
        with open(script_path, encoding="utf-8") as f:
            script = f.read()

        # Get language code
        voice = voice or self.config.voice
        lang_code = get_lang_code_from_voice(voice)

        # Smart chunking
        chunks = self._chunk_text_smart(script, lang_code=lang_code)

        total_tokens = sum(c.tokens for c in chunks)
        avg_tokens = total_tokens // len(chunks) if chunks else 0

        self.log.info(
            "script_parsed",
            num_chunks=len(chunks),
            total_tokens=total_tokens,
            avg_tokens=avg_tokens,
        )

        # Generate audio for each chunk
        audio_segments = []
        for chunk_info in chunks:
            self.log.info(
                "processing_chunk",
                chunk_num=chunk_info.index,
                total=chunk_info.total,
                tokens=chunk_info.tokens,
                preview=chunk_info.text[:50],
            )

            audio = self.generate(chunk_info.text, voice=voice, speed=speed)
            if isinstance(audio, Path):
                raise TTSGenerationError("Unexpected path return")
            audio_segments.append(audio)

        # Combine with gaps
        final_audio = combine_audio_segments(
            audio_segments,
            sample_rate=self.config.sample_rate,
            gap_duration=gap_duration,
        )

        # Save
        result_path = save_audio(
            final_audio,
            output_path,
            sample_rate=self.config.sample_rate,
            format=self.config.output_format,
        )

        duration = get_audio_duration(final_audio, self.config.sample_rate)
        self.log.info(
            "script_processed",
            path=str(result_path),
            chunks=len(chunks),
            duration=f"{duration:.2f}s",
        )

        return result_path

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    @staticmethod
    def list_voices() -> dict[str, list[str]]:
        """Get list of available voices by category.

        Returns:
            Dictionary with voice categories

        Example:
            >>> voices = TTSEngine.list_voices()
            >>> print(voices['male'])
        """
        return {
            "male": MALE_VOICES,
            "female": FEMALE_VOICES,
            "hindi_male": HINDI_MALE_VOICE_NAMES,
            "hindi_female": HINDI_FEMALE_VOICE_NAMES,
            "all": ALL_VOICES,
        }

    @staticmethod
    def get_voice_info(voice: str) -> VoiceInfo | None:
        """Get detailed information about a voice.

        Args:
            voice: Voice name

        Returns:
            VoiceInfo or None if not found

        Example:
            >>> info = TTSEngine.get_voice_info('af_sarah')
            >>> print(f"{info.description} ({info.accent})")
        """
        return VOICE_REGISTRY.get(voice)

    def get_supported_languages(self) -> dict[str, str]:
        """Get mapping of supported language codes to names.

        Returns:
            Dict of lang_code -> language name

        Example:
            >>> langs = engine.get_supported_languages()
            >>> print(langs['h'])  # 'Hindi'
        """
        return {
            "a": "American English",
            "b": "British English",
            "e": "Spanish",
            "f": "French",
            "h": "Hindi",
            "i": "Italian",
            "j": "Japanese",
            "p": "Brazilian Portuguese",
            "z": "Mandarin Chinese",
        }

    def estimate_duration(
        self,
        text: str,
        voice: str | None = None,
        speed: float | None = None,
    ) -> float:
        """Estimate audio duration for text without generating.

        Based on average speaking rate of ~150 words per minute at speed 1.0.

        Args:
            text: Input text
            voice: Voice (for token counting)
            speed: Speech speed factor

        Returns:
            Estimated duration in seconds

        Example:
            >>> duration = engine.estimate_duration("Hello world")
            >>> print(f"Estimated: {duration:.1f}s")
        """
        voice = voice or self.config.voice
        speed = speed or self.config.speed

        lang_code = get_lang_code_from_voice(voice)
        tokens = self._count_tokens(text, lang_code)

        # Kokoro generates ~5-6 phonemes per second at speed 1.0
        # Adjust for speed setting
        base_rate = 5.5  # phonemes per second
        adjusted_rate = base_rate * speed

        return tokens / adjusted_rate

    def __repr__(self) -> str:
        """String representation of engine."""
        return (
            f"TTSEngine("
            f"voice={self.config.voice!r}, "
            f"speed={self.config.speed}, "
            f"token_limits={self.config.token_target_min}-{self.config.token_target_max}"
            f")"
        )
