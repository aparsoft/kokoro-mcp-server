# aparsoft_tts/utils/__init__.py

"""Utility modules for Aparsoft TTS."""

from aparsoft_tts.utils.audio import (
    enhance_audio,
    combine_audio_segments,
    save_audio,
    load_audio,
    chunk_audio,
    get_audio_duration,
)
from aparsoft_tts.utils.exceptions import (
    AparsoftTTSError,
    ConfigurationError,
    AudioProcessingError,
    TTSGenerationError,
    ModelLoadError,
    InvalidVoiceError,
    InvalidParameterError,
    FileOperationError,
    MCPServerError,
)
from aparsoft_tts.utils.logging import (
    setup_logging,
    get_logger,
    bind_context,
    unbind_context,
    clear_context,
    LoggerMixin,
)

__all__ = [
    # Audio utilities
    "enhance_audio",
    "combine_audio_segments",
    "save_audio",
    "load_audio",
    "chunk_audio",
    "get_audio_duration",
    # Exceptions
    "AparsoftTTSError",
    "ConfigurationError",
    "AudioProcessingError",
    "TTSGenerationError",
    "ModelLoadError",
    "InvalidVoiceError",
    "InvalidParameterError",
    "FileOperationError",
    "MCPServerError",
    # Logging
    "setup_logging",
    "get_logger",
    "bind_context",
    "unbind_context",
    "clear_context",
    "LoggerMixin",
]
