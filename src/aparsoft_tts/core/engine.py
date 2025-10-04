"""Production-ready TTS engine using Kokoro TTS."""

from pathlib import Path
from typing import Generator, Iterator

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

# Available voices
MALE_VOICES = ["am_michael", "bm_george", "am_adam"]
FEMALE_VOICES = ["af_bella", "af_heart", "bf_emma"]
ALL_VOICES = MALE_VOICES + FEMALE_VOICES


class TTSEngine(LoggerMixin):
    """Production-ready TTS engine for YouTube video generation.

    This class provides a high-level interface to the Kokoro TTS model with:
    - Automatic audio enhancement
    - Batch processing capabilities
    - Streaming support
    - Error handling and logging
    - Configuration management

    Example:
        >>> from aparsoft_tts.core.engine import TTSEngine
        >>> engine = TTSEngine()
        >>> engine.generate("Hello world", "output.wav")
        PosixPath('output.wav')

        >>> # Batch processing
        >>> texts = ["Intro", "Main content", "Outro"]
        >>> engine.batch_generate(texts, "outputs/")

        >>> # Process full script
        >>> engine.process_script("script.txt", "final_voiceover.wav")
    """

    def __init__(self, config: TTSConfig | None = None):
        """Initialize TTS engine.

        Args:
            config: TTS configuration. If None, uses default config.

        Raises:
            ModelLoadError: If model fails to load
        """
        self.config = config or get_config().tts

        try:
            self.log.info(
                "initializing_tts_engine",
                voice=self.config.voice,
                lang_code=self.config.lang_code,
            )
            self.pipeline = KPipeline(lang_code=self.config.lang_code)
            self.log.info("tts_engine_initialized")
        except Exception as e:
            self.log.error("tts_initialization_failed", error=str(e))
            raise ModelLoadError(f"Failed to initialize TTS model: {e}") from e

    def generate(
        self,
        text: str,
        output_path: Path | str | None = None,
        voice: str | None = None,
        speed: float | None = None,
        enhance: bool | None = None,
    ) -> Path | NDArray[np.float32]:
        """Generate speech from text.

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
            self.log.info(
                "generating_speech",
                text_length=len(text),
                voice=voice,
                speed=speed,
                enhance=enhance,
            )

            # Generate speech
            generator = self.pipeline(text, voice=voice, speed=speed)

            audio_chunks = []
            for _, _, audio in generator:
                audio_chunks.append(audio)

            # Combine chunks
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
            self.log.info("generating_speech_stream", text_length=len(text), voice=voice)

            generator = self.pipeline(text, voice=voice, speed=speed)

            for _, _, audio in generator:
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
        """Process a complete video script file.

        Reads script, splits by paragraphs, generates audio for each,
        and combines with gaps.

        Args:
            script_path: Path to script text file
            output_path: Output file path
            gap_duration: Gap between segments in seconds
            voice: Voice to use (overrides config)
            speed: Speech speed (overrides config)

        Returns:
            Path to output file

        Raises:
            TTSGenerationError: If processing fails
            FileNotFoundError: If script file not found

        Example:
            >>> engine = TTSEngine()
            >>> engine.process_script("script.txt", "voiceover.wav")
        """
        script_path = Path(script_path)

        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")

        self.log.info("processing_script", script_path=str(script_path))

        # Read and split script
        with open(script_path, "r", encoding="utf-8") as f:
            script = f.read()

        segments = [s.strip() for s in script.split("\n\n") if s.strip()]
        self.log.info("script_parsed", num_segments=len(segments))

        # Generate segments
        audio_segments = []
        for i, segment in enumerate(segments, 1):
            self.log.info("processing_segment", segment_num=i, text_length=len(segment))

            audio = self.generate(segment, voice=voice, speed=speed)
            if isinstance(audio, Path):
                # This shouldn't happen since we're not passing output_path
                raise TTSGenerationError("Unexpected path return from generate")

            audio_segments.append(audio)

        # Combine segments
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
            num_segments=len(segments),
            duration_seconds=duration,
        )

        return result_path

    @staticmethod
    def list_voices() -> dict[str, list[str]]:
        """Get list of available voices.

        Returns:
            Dictionary with 'male' and 'female' voice lists

        Example:
            >>> voices = TTSEngine.list_voices()
            >>> print(voices['male'])
            ['am_michael', 'bm_george', 'am_adam']
        """
        return {"male": MALE_VOICES, "female": FEMALE_VOICES}
