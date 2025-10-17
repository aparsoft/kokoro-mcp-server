# aparsoft_tts/core/engine.py

"""Comprehensive TTS engine using Kokoro TTS with intelligent chunking.

This module provides a high-level TTSEngine class that interfaces with the Kokoro TTS
model. It includes advanced features such as automatic token counting, intelligent
chunking of long texts, audio enhancement, batch processing, and streaming support.

Key functionality:
- Automatic token counting and intelligent chunking for long texts
- Audio enhancement with professional processing
- Batch processing capabilities
- Streaming support
- Error handling and logging
- Configuration management
"""

import re
from pathlib import Path
from typing import Iterator

import numpy as np
from kokoro import KPipeline
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

# Available voices from Kokoro-82M
# Source: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md

# English voices
MALE_VOICES = [
    "am_adam",  # American male - natural inflection
    "am_michael",  # American male - deeper tones (professional)
    "bm_george",  # British male - classic accent
    "bm_lewis",  # British male - modern accent
]

FEMALE_VOICES = [
    "af_bella",  # American female - warm tones
    "af_nicole",  # American female - dynamic range
    "af_sarah",  # American female - clear articulation
    "af_sky",  # American female - youthful energy
    "bf_emma",  # British female - professional
    "bf_isabella",  # British female - soft tones
]

# Special voice (50-50 mix of Bella and Sarah)
SPECIAL_VOICES = [
    "af",  # Default American female (Bella + Sarah mix)
]

# Hindi voices (lang_code='h', requires espeak-ng with hi)
HINDI_MALE_VOICES = [
    "hm_omega",  # Hindi male - voice omega
    "hm_psi",  # Hindi male - voice psi
]

HINDI_FEMALE_VOICES = [
    "hf_alpha",  # Hindi female - voice alpha
    "hf_beta",  # Hindi female - voice beta
]

ALL_VOICES = MALE_VOICES + FEMALE_VOICES + SPECIAL_VOICES + HINDI_MALE_VOICES + HINDI_FEMALE_VOICES


def get_lang_code_from_voice(voice: str) -> str:
    """Get the correct lang_code for a voice based on its prefix.

    Kokoro requires lang_code to match voice prefix:
    - am_/af_ (American) -> 'a'
    - bm_/bf_ (British) -> 'b'
    - hm_/hf_ (Hindi) -> 'h'
    - jm_/jf_ (Japanese) -> 'j'
    - zm_/zf_ (Chinese) -> 'z'
    - em_/ef_ (Spanish) -> 'e'
    - im_/if_ (Italian) -> 'i'
    - pm_/pf_ (Portuguese) -> 'p'
    - fm_/ff_ (French) -> 'f'

    Args:
        voice: Voice name (e.g., 'am_michael', 'hf_alpha', 'bm_george')

    Returns:
        Lang code: 'a' for American English, 'b' for British English,
                   'h' for Hindi, etc.

    Example:
        >>> get_lang_code_from_voice('am_michael')
        'a'
        >>> get_lang_code_from_voice('hf_alpha')
        'h'
        >>> get_lang_code_from_voice('bm_george')
        'b'
    """
    if voice.startswith(("am_", "af_")):
        return "a"  # American English
    elif voice.startswith(("bm_", "bf_")):
        return "b"  # British English
    elif voice.startswith(("hm_", "hf_")):
        return "h"  # Hindi
    elif voice.startswith(("jm_", "jf_")):
        return "j"  # Japanese
    elif voice.startswith(("zm_", "zf_")):
        return "z"  # Mandarin Chinese
    elif voice.startswith(("em_", "ef_")):
        return "e"  # Spanish
    elif voice.startswith(("im_", "if_")):
        return "i"  # Italian
    elif voice.startswith(("pm_", "pf_")):
        return "p"  # Brazilian Portuguese
    elif voice.startswith(("fm_", "ff_")):
        return "f"  # French
    else:
        # Fallback to first letter if voice format is non-standard
        return voice[0] if voice and voice[0] in "abhjzeipf" else "a"


class TTSEngine(LoggerMixin):
    """Comprehensive TTS engine with intelligent token-aware chunking.

    This class provides a high-level interface to the Kokoro TTS model with:
    - Automatic token counting and intelligent chunking
    - Audio enhancement with professional processing
    - Batch processing capabilities
    - Streaming support
    - Error handling and logging
    - Configuration management

    Kokoro Model Limits:
        - Maximum: 510 tokens per pass (architectural limit)
        - Optimal: 100-250 tokens (best audio quality)
        - Rushed speech: >400 tokens (quality degrades)

    The engine automatically chunks long texts at sentence boundaries
    to maintain optimal quality and prevent rushed speech artifacts.

    Token limits are configurable via TTSConfig:
        - token_target_min: Minimum tokens per chunk (default: 100)
        - token_target_max: Target maximum (default: 250)
        - token_absolute_max: Hard limit (default: 450)
        - chunk_gap_duration: Gap between chunks (default: 0.2s)

    Example:
        >>> from aparsoft_tts.core.engine import TTSEngine
        >>> engine = TTSEngine()
        >>> engine.generate("Hello world", "output.wav")
        PosixPath('output.wav')

        >>> # Long text automatically chunked
        >>> long_text = "..." * 1000  # Very long text
        >>> engine.generate(long_text, "output.wav")  # Handles chunking

        >>> # Custom token limits via config
        >>> from aparsoft_tts import TTSConfig
        >>> config = TTSConfig(token_target_max=300)  # Larger chunks
        >>> engine = TTSEngine(config=config)
    """

    def __init__(self, config: TTSConfig | None = None):
        """Initialize TTS engine.

        Args:
            config: TTS configuration. If None, uses default config.

        Raises:
            ModelLoadError: If model fails to load
        """
        self.config = config or get_config().tts

        # Cache for KPipeline instances per lang_code
        # This prevents recreating pipelines and improves performance
        self._pipelines: dict[str, KPipeline] = {}
        self.repo_id = self.config.repo_id

        try:
            self.log.info(
                "initializing_tts_engine",
                voice=self.config.voice,
                token_limits=f"{self.config.token_target_min}-{self.config.token_target_max}",
            )
            # Initialize pipeline for default voice's lang_code
            default_lang = get_lang_code_from_voice(self.config.voice)
            self._get_pipeline(default_lang)
            self.log.info("tts_engine_initialized", default_lang_code=default_lang)
        except Exception as e:
            self.log.error("tts_initialization_failed", error=str(e))
            raise ModelLoadError(f"Failed to initialize TTS model: {e}") from e

    def _get_pipeline(self, lang_code: str) -> KPipeline:
        """Get or create a KPipeline for the specified lang_code.

        Pipelines are cached to avoid recreation overhead.

        Args:
            lang_code: Language code ('a' or 'b')

        Returns:
            KPipeline instance for the lang_code
        """
        if lang_code not in self._pipelines:
            self.log.debug("creating_pipeline", lang_code=lang_code)
            self._pipelines[lang_code] = KPipeline(lang_code=lang_code, repo_id=self.repo_id)
        return self._pipelines[lang_code]

    def _count_tokens(self, text: str, lang_code: str = "a") -> int:
        """Count phonemized tokens for text.

        Uses Kokoro's pipeline G2P to get accurate token count.
        This is critical for preventing rushed speech.

        Args:
            text: Input text
            lang_code: Language code for phonemization

        Returns:
            Number of phonemized tokens

        Note:
            Falls back to rough estimate (1 token ≈ 4 chars) if
            phonemization fails.
        """
        try:
            # Get the pipeline for this language
            pipeline = self._get_pipeline(lang_code)

            # Use pipeline's G2P to get phonemes
            # For English (lang_code 'a' or 'b'), g2p returns (phonemes, tokens)
            if lang_code in "ab":
                ps, tokens = pipeline.g2p(text)
                # Return phoneme count
                return len(ps) if ps else 0
            else:
                # For other languages, g2p returns (phonemes, _)
                ps, _ = pipeline.g2p(text)
                return len(ps) if ps else 0

        except Exception as e:
            # Fallback: rough estimate
            # Average: 1 token ≈ 4 characters for English
            self.log.warning("token_count_fallback", error=str(e), using_estimate=True)
            return len(text) // 4

    def _chunk_text_smart(
        self,
        text: str,
        target_min_tokens: int | None = None,
        target_max_tokens: int | None = None,
        absolute_max_tokens: int | None = None,
    ) -> list[str]:
        """Chunk text intelligently based on token limits.

        Implements best practices for Kokoro TTS:
        - Optimal range: 100-250 tokens per chunk (configurable)
        - Never exceed hard limit (prevents rushed speech)
        - Split at sentence boundaries when possible
        - Avoid very short chunks (<20 tokens)
        - Handle edge cases (oversized sentences, etc.)

        Algorithm:
            1. Split text into sentences
            2. Combine sentences until target_max_tokens
            3. For oversized sentences, split by commas/semicolons
            4. Last resort: force split by words
            5. Merge very short final chunks with previous

        Args:
            text: Input text to chunk
            target_min_tokens: Minimum tokens per chunk (default: from config)
            target_max_tokens: Target maximum tokens per chunk (default: from config)
            absolute_max_tokens: Hard limit to prevent rushed speech (default: from config)

        Returns:
            List of text chunks, each within optimal token range

        Example:
            >>> engine = TTSEngine()
            >>> chunks = engine._chunk_text_smart("Long text here...")
            >>> # Each chunk uses configured token limits
        """
        # Use config values if not provided
        target_min_tokens = target_min_tokens or self.config.token_target_min
        target_max_tokens = target_max_tokens or self.config.token_target_max
        absolute_max_tokens = absolute_max_tokens or self.config.token_absolute_max

        # Split into sentences first
        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_tokens = self._count_tokens(sentence)

            # Handle oversized single sentences
            if sentence_tokens > absolute_max_tokens:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                # Split long sentence by commas/semicolons
                parts = re.split(r"[,;]\s+", sentence)
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue

                    part_tokens = self._count_tokens(part)

                    if part_tokens > absolute_max_tokens:
                        # Force split by words as last resort
                        words = part.split()
                        for word in words:
                            word_tokens = self._count_tokens(word)
                            if current_tokens + word_tokens <= target_max_tokens:
                                current_chunk.append(word)
                                current_tokens += word_tokens
                            else:
                                if current_chunk:
                                    chunks.append(" ".join(current_chunk))
                                current_chunk = [word]
                                current_tokens = word_tokens
                    else:
                        if current_tokens + part_tokens <= target_max_tokens:
                            current_chunk.append(part)
                            current_tokens += part_tokens
                        else:
                            if current_chunk:
                                chunks.append(" ".join(current_chunk))
                            current_chunk = [part]
                            current_tokens = part_tokens
                continue

            # Normal sentence handling
            if current_tokens + sentence_tokens <= target_max_tokens:
                # Add to current chunk
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
            else:
                # Start new chunk
                if current_chunk:
                    # Only save if meets minimum threshold
                    if current_tokens >= target_min_tokens or len(chunks) == 0:
                        chunks.append(" ".join(current_chunk))
                    else:
                        # Chunk too small, merge with previous if possible
                        if chunks:
                            chunks[-1] += " " + " ".join(current_chunk)

                current_chunk = [sentence]
                current_tokens = sentence_tokens

        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            # Avoid very short chunks (< 20 tokens)
            if current_tokens >= 20 or len(chunks) == 0:
                chunks.append(chunk_text)
            elif chunks:
                # Merge with previous chunk
                chunks[-1] += " " + chunk_text

        return chunks

    def generate(
        self,
        text: str,
        output_path: Path | str | None = None,
        voice: str | None = None,
        speed: float | None = None,
        enhance: bool | None = None,
    ) -> Path | NDArray[np.float32]:
        """Generate speech from text with automatic intelligent chunking.

        For texts over token_target_max, automatically chunks at sentence
        boundaries to maintain optimal audio quality and prevent
        rushed speech artifacts.

        Args:
            text: Input text to convert to speech
            output_path: Output file path. If None, returns audio array.
            voice: Voice to use (overrides config). Must be in ALL_VOICES.
            speed: Speech speed (overrides config). Range: 0.5-2.0.
            enhance: Apply audio enhancement (overrides config)

        Returns:
            Path to saved file if output_path provided, else audio array

        Raises:
            TTSGenerationError: If generation fails
            InvalidVoiceError: If voice is invalid
            InvalidParameterError: If parameters are invalid

        Example:
            >>> engine = TTSEngine()
            >>> path = engine.generate("Hello", "output.wav")
            >>> audio = engine.generate("Hello")  # Returns array

            >>> # Long text automatically chunked for quality
            >>> long_text = "..." * 500
            >>> engine.generate(long_text, "long_output.wav")
        """
        # Validate parameters
        voice = voice or self.config.voice
        if voice not in ALL_VOICES:
            raise InvalidVoiceError(
                f"Invalid voice: {voice}. Must be one of: {', '.join(ALL_VOICES)}"
            )

        speed = speed if speed is not None else self.config.speed
        if not 0.5 <= speed <= 2.0:
            raise InvalidParameterError(f"Speed must be between 0.5 and 2.0, got {speed}")

        enhance = enhance if enhance is not None else self.config.enhance_audio

        try:
            # Get correct lang_code for voice
            voice_lang_code = get_lang_code_from_voice(voice)

            # Get appropriate pipeline for this voice
            pipeline = self._get_pipeline(voice_lang_code)

            # Count tokens with correct lang_code
            token_count = self._count_tokens(text, voice_lang_code)

            self.log.info(
                "generating_speech",
                text_length=len(text),
                estimated_tokens=token_count,
                voice=voice,
                speed=speed,
                enhance=enhance,
            )

            # Chunk if text exceeds optimal length
            if token_count > self.config.token_target_max:
                self.log.info(
                    "text_exceeds_optimal_length_chunking",
                    tokens=token_count,
                    target_max=self.config.token_target_max,
                )

                chunks = self._chunk_text_smart(text)

                audio_chunks = []
                for i, chunk in enumerate(chunks):
                    chunk_tokens = self._count_tokens(chunk)
                    self.log.debug(
                        "processing_chunk",
                        chunk_num=i + 1,
                        total_chunks=len(chunks),
                        tokens=chunk_tokens,
                        text_preview=chunk[:50],
                    )

                    # Generate for this chunk using correct pipeline
                    generator = pipeline(chunk, voice=voice, speed=speed)
                    chunk_audio = []
                    for _, _, audio in generator:
                        if hasattr(audio, "cpu"):
                            audio = audio.cpu().numpy()
                        chunk_audio.append(audio)

                    audio_chunks.append(np.concatenate(chunk_audio).astype(np.float32))

                # Combine with configured gap to prevent artifacts
                final_audio = combine_audio_segments(
                    audio_chunks,
                    sample_rate=self.config.sample_rate,
                    gap_duration=self.config.chunk_gap_duration,
                )

                self.log.info(
                    "chunks_combined", num_chunks=len(chunks), total_samples=len(final_audio)
                )
            else:
                # Text within optimal range - generate directly
                generator = pipeline(text, voice=voice, speed=speed)

                audio_chunks = []
                for _, _, audio in generator:
                    if hasattr(audio, "cpu"):
                        audio = audio.cpu().numpy()
                    audio_chunks.append(audio)

                final_audio = np.concatenate(audio_chunks).astype(np.float32)

            # Enhance if requested
            if enhance:
                final_audio = enhance_audio(
                    final_audio,
                    sample_rate=self.config.sample_rate,
                    trim_silence=self.config.trim_silence,
                    trim_db=self.config.trim_db,
                    fade_duration=self.config.fade_duration,
                )

            duration = get_audio_duration(final_audio, self.config.sample_rate)
            self.log.info("speech_generated", duration_seconds=duration, samples=len(final_audio))

            # Save or return
            if output_path:
                return save_audio(
                    final_audio,
                    output_path,
                    sample_rate=self.config.sample_rate,
                    format=self.config.output_format,
                )
            else:
                return final_audio

        except (InvalidVoiceError, InvalidParameterError):
            raise
        except Exception as e:
            self.log.error("speech_generation_failed", error=str(e), text_preview=text[:50])
            raise TTSGenerationError(f"Failed to generate speech: {e}") from e

    def generate_stream(
        self, text: str, voice: str | None = None, speed: float | None = None
    ) -> Iterator[NDArray[np.float32]]:
        """Generate speech as a stream of audio chunks.

        Useful for real-time applications or processing long texts.
        Automatically chunks text if it exceeds optimal token limits.

        Args:
            text: Input text
            voice: Voice to use (overrides config)
            speed: Speech speed (overrides config)

        Yields:
            Audio chunks as they're generated

        Raises:
            TTSGenerationError: If generation fails

        Example:
            >>> engine = TTSEngine()
            >>> for chunk in engine.generate_stream("Long text..."):
            ...     process_chunk(chunk)
        """
        voice = voice or self.config.voice
        speed = speed if speed is not None else self.config.speed

        try:
            # Get correct pipeline for voice
            voice_lang_code = get_lang_code_from_voice(voice)
            pipeline = self._get_pipeline(voice_lang_code)

            token_count = self._count_tokens(text, voice_lang_code)
            self.log.info(
                "generating_speech_stream",
                text_length=len(text),
                estimated_tokens=token_count,
                voice=voice,
                lang_code=voice_lang_code,
            )

            # Chunk if needed
            if token_count > self.config.token_target_max:
                chunks = self._chunk_text_smart(text)
                for chunk in chunks:
                    generator = pipeline(chunk, voice=voice, speed=speed)
                    for _, _, audio in generator:
                        if hasattr(audio, "cpu"):
                            audio = audio.cpu().numpy()
                        yield audio.astype(np.float32)
            else:
                # Direct generation for short text
                generator = pipeline(text, voice=voice, speed=speed)
                for _, _, audio in generator:
                    if hasattr(audio, "cpu"):
                        audio = audio.cpu().numpy()
                    yield audio.astype(np.float32)

        except Exception as e:
            self.log.error("stream_generation_failed", error=str(e))
            raise TTSGenerationError(f"Failed to generate speech stream: {e}") from e

    def batch_generate(
        self,
        texts: list[str],
        output_dir: Path | str,
        voice: str | None = None,
        speed: float | None = None,
        filename_prefix: str = "audio",
    ) -> list[Path]:
        """Generate multiple audio files from a list of texts.

        Each text is automatically chunked if needed for optimal quality.

        Args:
            texts: List of text strings to convert
            output_dir: Output directory for audio files
            voice: Voice to use (overrides config)
            speed: Speech speed (overrides config)
            filename_prefix: Prefix for output filenames

        Returns:
            List of paths to generated files

        Raises:
            TTSGenerationError: If generation fails

        Example:
            >>> engine = TTSEngine()
            >>> texts = ["Intro", "Body", "Outro"]
            >>> paths = engine.batch_generate(texts, "outputs/")
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        self.log.info("batch_generation_started", num_texts=len(texts), output_dir=str(output_dir))

        paths = []
        for i, text in enumerate(texts, 1):
            output_file = output_dir / f"{filename_prefix}_{i:03d}.{self.config.output_format}"

            try:
                path = self.generate(text, output_file, voice=voice, speed=speed)
                paths.append(path)
                self.log.info("batch_item_generated", index=i, path=str(path))
            except Exception as e:
                self.log.error("batch_item_failed", index=i, error=str(e))
                raise

        self.log.info("batch_generation_completed", num_files=len(paths))
        return paths

    def process_script(
        self,
        script_path: Path | str,
        output_path: Path | str,
        gap_duration: float = 0.5,
        voice: str | None = None,
        speed: float | None = None,
    ) -> Path:
        """Process a complete video script file with intelligent chunking.

        Reads script, applies token-aware chunking for optimal quality,
        generates audio for each chunk, and combines with gaps.

        The chunking algorithm ensures:
        - Each chunk is within configured token limits
        - No chunk exceeds hard limit (prevents rushed speech)
        - Splits at sentence boundaries when possible
        - Maintains natural phrasing and rhythm

        Args:
            script_path: Path to script text file
            output_path: Output file path
            gap_duration: Gap between segments in seconds (default: 0.5s)
            voice: Voice to use (overrides config)
            speed: Speech speed (overrides config)

        Returns:
            Path to output file

        Raises:
            TTSGenerationError: If processing fails
            FileNotFoundError: If script file not found

        Example:
            >>> engine = TTSEngine()
            >>> # Script automatically chunked for best quality
            >>> engine.process_script("long_script.txt", "voiceover.wav")
        """
        script_path = Path(script_path)

        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")

        self.log.info("processing_script", script_path=str(script_path))

        # Read script
        with open(script_path, "r", encoding="utf-8") as f:
            script = f.read()

        # Smart chunking for optimal token distribution
        chunks = self._chunk_text_smart(script)

        total_tokens = sum(self._count_tokens(c) for c in chunks)
        self.log.info(
            "script_parsed",
            num_chunks=len(chunks),
            estimated_total_tokens=total_tokens,
            avg_tokens_per_chunk=total_tokens // len(chunks) if chunks else 0,
        )

        # Generate chunks
        audio_segments = []
        for i, chunk in enumerate(chunks, 1):
            tokens = self._count_tokens(chunk)
            self.log.info(
                "processing_chunk",
                chunk_num=i,
                total_chunks=len(chunks),
                tokens=tokens,
                text_length=len(chunk),
                text_preview=chunk[:50],
            )

            audio = self.generate(chunk, voice=voice, speed=speed)
            if isinstance(audio, Path):
                # This shouldn't happen since we're not passing output_path
                raise TTSGenerationError("Unexpected path return from generate")

            audio_segments.append(audio)

        # Combine segments with gaps
        final_audio = combine_audio_segments(
            audio_segments, sample_rate=self.config.sample_rate, gap_duration=gap_duration
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
            output_path=str(result_path),
            num_chunks=len(chunks),
            duration_seconds=duration,
        )

        return result_path

    @staticmethod
    def list_voices() -> dict[str, list[str]]:
        """Get list of available voices.

        Returns:
            Dictionary with voice categories:
            - 'male': English male voices
            - 'female': English female voices
            - 'hindi_male': Hindi male voices
            - 'hindi_female': Hindi female voices
            - 'all': All available voices

        Example:
            >>> voices = TTSEngine.list_voices()
            >>> print(voices['male'])
            ['am_michael', 'bm_george', 'am_adam']
            >>> print(voices['hindi_female'])
            ['hf_alpha', 'hf_beta']
        """
        return {
            "male": MALE_VOICES,
            "female": FEMALE_VOICES,
            "hindi_male": HINDI_MALE_VOICES,
            "hindi_female": HINDI_FEMALE_VOICES,
            "all": ALL_VOICES,
        }
