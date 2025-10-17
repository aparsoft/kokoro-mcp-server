# aparsoft_tts/__init__.py

"""Aparsoft TTS - Comprehensive Text-to-Speech with THREE powerful engines.

This package provides a comprehensive TTS solution with THREE engines:

1. **Kokoro TTS** (Default): Fast, high-quality English TTS
   - 11 professional voices (male/female, US/UK)
   - Optimized for speed and English quality
   - 82M parameters, efficient

2. **OpenVoice V2**: Multilingual voice cloning
   - Zero-shot cloning from 3-5s reference audio
   - 6 languages: EN, ES, FR, ZH, JA, KO
   - Cross-lingual capability

3. **Indic Parler-TTS**: Professional Indian language TTS
   - 21 Indic languages (Hindi, Bengali, Tamil, etc.)
   - 69 professional voices
   - Hindi quality: 83.43 MOS
   - Emotion control (10 emotions)

Basic Usage (Kokoro):
    >>> from aparsoft_tts import TTSEngine
    >>> engine = TTSEngine()
    >>> engine.generate("Hello world", "output.wav")

Indic Usage:
    >>> from aparsoft_tts import get_tts_engine
    >>> engine = get_tts_engine("indic")
    >>> engine.generate(
    ...     "नमस्ते दोस्तों!",
    ...     "output.wav",
    ...     voice="divya",
    ...     emotion="happy"
    ... )

OpenVoice Usage:
    >>> engine = get_tts_engine("openvoice")
    >>> engine.generate_with_cloning(
    ...     "Your text",
    ...     "reference.wav",
    ...     "cloned.wav"
    ... )

Factory Pattern:
    >>> from aparsoft_tts import get_tts_engine
    >>> # Uses ENGINE env var or config (kokoro/openvoice/indic)
    >>> engine = get_tts_engine()
"""

__version__ = "1.0.0"
__author__ = "Aparsoft"
__email__ = "contact@aparsoft.com"

# Core imports
from aparsoft_tts.core.engine import TTSEngine, ALL_VOICES, MALE_VOICES, FEMALE_VOICES
from aparsoft_tts.config import Config, TTSConfig, MCPConfig, LoggingConfig, get_config

# Factory pattern for engine selection
from aparsoft_tts.core.engine_factory import (
    get_tts_engine,
    get_engine_info,
    list_available_engines,
    compare_engines,
)

# OpenVoice (optional, imported dynamically)
# If you need OpenVoice, use:
#   from aparsoft_tts.engine_openvoice import OpenVoiceEngine
#   from aparsoft_tts.config_openvoice import OpenVoiceConfig

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
    "TTSEngine",  # Kokoro engine (default)
    # Factory pattern
    "get_tts_engine",  # Get engine by type
    "get_engine_info",  # Get engine information
    "list_available_engines",  # List all engines
    "compare_engines",  # Compare engine capabilities
    # Voice lists (Kokoro)
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
    # Note: OpenVoiceEngine and OpenVoiceConfig available via:
    #   from aparsoft_tts.engine_openvoice import OpenVoiceEngine
    #   from aparsoft_tts.config_openvoice import OpenVoiceConfig
]
