"""Aparsoft TTS - Production-Ready Text-to-Speech for YouTube Videos.

This package provides a comprehensive TTS solution using Kokoro TTS models
with professional audio enhancement, MCP server integration, and enterprise-grade
features like logging, configuration management, and error handling.

Basic Usage:
    >>> from aparsoft_tts import TTSEngine
    >>> engine = TTSEngine()
    >>> engine.generate("Hello world", "output.wav")

Advanced Usage:
    >>> from aparsoft_tts import TTSEngine, TTSConfig
    >>> config = TTSConfig(voice="am_michael", speed=1.2)
    >>> engine = TTSEngine(config=config)
    >>> engine.process_script("script.txt", "voiceover.wav")
"""

__version__ = "1.0.0"
__author__ = "Aparsoft"
__email__ = "contact@aparsoft.com"

# Core imports
from aparsoft_tts.core.engine import TTSEngine, ALL_VOICES, MALE_VOICES, FEMALE_VOICES
from aparsoft_tts.config import Config, TTSConfig, MCPConfig, LoggingConfig, get_config

# Utility imports
from aparsoft_tts.utils.exceptions import (
    AparsoftTTSError,
    AudioProcessingError,
    TTSGenerationError,
    ModelLoadError,
    InvalidVoiceError,
    InvalidParameterError,
    FileOperationError,
    MCPServerError,
)

# Setup logging on import
from aparsoft_tts.utils.logging import setup_logging

# Initialize logging with default configuration
try:
    setup_logging()
except Exception:
    # Don't fail if logging setup fails
    pass

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Core classes
    "TTSEngine",
    # Voice lists
    "ALL_VOICES",
    "MALE_VOICES",
    "FEMALE_VOICES",
    # Configuration
    "Config",
    "TTSConfig",
    "MCPConfig",
    "LoggingConfig",
    "get_config",
    # Exceptions
    "AparsoftTTSError",
    "AudioProcessingError",
    "TTSGenerationError",
    "ModelLoadError",
    "InvalidVoiceError",
    "InvalidParameterError",
    "FileOperationError",
    "MCPServerError",
]
