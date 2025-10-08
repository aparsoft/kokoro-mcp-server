"""Factory pattern for TTS engine selection.

This module provides a unified interface to select and initialize
either Kokoro or OpenVoice engines based on configuration.

Usage:
    from aparsoft_tts.engine_factory import get_tts_engine

    # Get engine based on config
    engine = get_tts_engine()  # Uses ENGINE env var or config

    # Or specify explicitly
    kokoro = get_tts_engine("kokoro")
    openvoice = get_tts_engine("openvoice")

    # Use the engine
    engine.generate("Hello world", "output.wav")
"""

from typing import Literal, Union

from aparsoft_tts.config import get_config
from aparsoft_tts.utils.logging import get_logger

log = get_logger(__name__)

# Type alias for engine types
EngineType = Literal["kokoro", "openvoice"]


def get_tts_engine(
    engine_type: EngineType | None = None,
) -> Union["TTSEngine", "OpenVoiceEngine"]:  # noqa: F821
    """Factory function to get TTS engine based on type.

    This function creates and returns the appropriate TTS engine instance
    based on the specified engine type or configuration.

    Engine Comparison:
        - **kokoro**: Fast, high-quality English TTS with pre-defined voices
          - Best for: Speed, English content, professional voices
          - Languages: English (US/UK)
          - Voices: 11 pre-defined professional voices

        - **openvoice**: Multilingual voice cloning with zero-shot capability
          - Best for: Voice cloning, multilingual, cross-lingual
          - Languages: EN, ES, FR, ZH, JA, KO
          - Voices: Clone ANY voice from 3-5s reference audio

    Args:
        engine_type: Type of engine to use. If None, uses config setting.
                    Options: "kokoro" or "openvoice"

    Returns:
        TTSEngine (Kokoro) or OpenVoiceEngine instance

    Raises:
        ValueError: If invalid engine type specified
        ImportError: If engine dependencies not installed
        ModelLoadError: If engine fails to initialize

    Example:
        >>> # Use configured engine
        >>> engine = get_tts_engine()
        >>>
        >>> # Use specific engine
        >>> kokoro = get_tts_engine("kokoro")
        >>> kokoro.generate("Fast English TTS", "output.wav")
        >>>
        >>> openvoice = get_tts_engine("openvoice")
        >>> openvoice.generate_with_cloning(
        ...     "Cloned voice",
        ...     "reference.wav",
        ...     "cloned.wav"
        ... )
    """
    # Get engine type from config if not specified
    if engine_type is None:
        config = get_config()
        engine_type = config.engine

    log.info("initializing_tts_engine", engine_type=engine_type)

    # Validate engine type
    if engine_type not in ("kokoro", "openvoice"):
        raise ValueError(f"Invalid engine type: {engine_type}. Must be 'kokoro' or 'openvoice'")

    # Import and initialize appropriate engine
    if engine_type == "kokoro":
        from aparsoft_tts.core.engine import TTSEngine

        log.info("using_kokoro_engine")
        return TTSEngine()

    elif engine_type == "openvoice":
        try:
            from aparsoft_tts.openvoice_engine import OpenVoiceEngine

            log.info("using_openvoice_engine")
            return OpenVoiceEngine()

        except ImportError as e:
            log.error("openvoice_import_failed", error=str(e))
            raise ImportError(
                f"OpenVoice engine not available: {e}\n\n"
                f"To install OpenVoice:\n"
                f'  1. pip install -e ".[openvoice]"\n'
                f"  2. pip install git+https://github.com/myshell-ai/MeloTTS.git\n"
                f"  3. python -m aparsoft_tts.download_openvoice_checkpoints\n\n"
                f"See README_OPENVOICE.md for details."
            ) from e


def get_engine_info(engine_type: EngineType) -> dict:
    """Get information about an engine type.

    Args:
        engine_type: Engine type to get info for

    Returns:
        Dictionary with engine information

    Example:
        >>> info = get_engine_info("kokoro")
        >>> print(info["description"])
        Fast, high-quality English TTS with pre-defined voices
    """
    engines = {
        "kokoro": {
            "name": "Kokoro TTS",
            "description": "Fast, high-quality English TTS with pre-defined voices",
            "languages": ["English (US)", "English (UK)"],
            "language_codes": ["en-us", "en-gb"],
            "voices": 11,
            "features": [
                "Fast generation",
                "Pre-defined professional voices",
                "Intelligent text chunking",
                "High-quality English synthesis",
            ],
            "best_for": [
                "English YouTube tutorials",
                "Podcasts with consistent voices",
                "Fast content generation",
                "Professional English voiceovers",
            ],
            "model_size": "82M parameters",
            "license": "Apache 2.0",
        },
        "openvoice": {
            "name": "OpenVoice V2",
            "description": "Multilingual zero-shot voice cloning",
            "languages": [
                "English",
                "Spanish",
                "French",
                "Chinese (Mandarin)",
                "Japanese",
                "Korean",
            ],
            "language_codes": ["en", "es", "fr", "zh", "ja", "ko"],
            "voices": "Unlimited (clone any voice)",
            "features": [
                "Zero-shot voice cloning",
                "Cross-lingual generation",
                "Flexible style control",
                "Emotion/accent adjustment",
                "Clone from 3-5s reference audio",
            ],
            "best_for": [
                "Voice cloning and personalization",
                "Multilingual content",
                "Cross-lingual dubbing",
                "Brand voice consistency",
            ],
            "model_size": "Multiple models (larger)",
            "license": "MIT",
        },
    }

    return engines.get(engine_type, {})


def list_available_engines() -> dict[str, dict]:
    """List all available TTS engines and their capabilities.

    Returns:
        Dictionary mapping engine names to their information

    Example:
        >>> engines = list_available_engines()
        >>> for name, info in engines.items():
        ...     print(f"{name}: {info['description']}")
    """
    return {
        "kokoro": get_engine_info("kokoro"),
        "openvoice": get_engine_info("openvoice"),
    }


def compare_engines() -> str:
    """Get a formatted comparison of available engines.

    Returns:
        Formatted string comparing engines

    Example:
        >>> print(compare_engines())
    """
    kokoro_info = get_engine_info("kokoro")
    openvoice_info = get_engine_info("openvoice")

    comparison = f"""
╔══════════════════════════════════════════════════════════════╗
║              TTS Engine Comparison                          ║
╚══════════════════════════════════════════════════════════════╝

🐈 KOKORO TTS
  Description: {kokoro_info['description']}
  Languages: {', '.join(kokoro_info['languages'])}
  Voices: {kokoro_info['voices']} pre-defined professional voices
  Model Size: {kokoro_info['model_size']}
  License: {kokoro_info['license']}
  
  ✨ Features:
"""
    for feature in kokoro_info["features"]:
        comparison += f"    • {feature}\n"

    comparison += f"""
  🎯 Best For:
"""
    for use_case in kokoro_info["best_for"]:
        comparison += f"    • {use_case}\n"

    comparison += f"""
───────────────────────────────────────────────────────────────

🎙️ OPENVOICE V2
  Description: {openvoice_info['description']}
  Languages: {', '.join(openvoice_info['languages'])}
  Voices: {openvoice_info['voices']}
  Model Size: {openvoice_info['model_size']}
  License: {openvoice_info['license']}
  
  ✨ Features:
"""
    for feature in openvoice_info["features"]:
        comparison += f"    • {feature}\n"

    comparison += f"""
  🎯 Best For:
"""
    for use_case in openvoice_info["best_for"]:
        comparison += f"    • {use_case}\n"

    comparison += """
───────────────────────────────────────────────────────────────

💡 QUICK DECISION GUIDE:

Choose Kokoro if you need:
  ✓ Fast generation
  ✓ English-only content
  ✓ Professional pre-defined voices
  ✓ Simple setup

Choose OpenVoice if you need:
  ✓ Voice cloning capability
  ✓ Multilingual content (6 languages)
  ✓ Cross-lingual dubbing
  ✓ Your own or custom voices

Both engines can be used in the same project!
Switch with: ENGINE=kokoro or ENGINE=openvoice in .env

"""
    return comparison


if __name__ == "__main__":
    print(compare_engines())

    print("\n🔧 Testing Engine Factory...")

    # Test engine selection
    config = get_config()
    print(f"\n📊 Current config: ENGINE={config.engine}")

    try:
        engine = get_tts_engine()
        print(f"✅ Successfully loaded {config.engine} engine")
        print(f"   Engine type: {type(engine).__name__}")
    except Exception as e:
        print(f"❌ Failed to load engine: {e}")

    print("\n📚 For more information:")
    print("   Kokoro: See README.md")
    print("   OpenVoice: See README_OPENVOICE.md")
