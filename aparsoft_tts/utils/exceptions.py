# aparsoft_tts/utils/exceptions.py

"""Custom exceptions for Aparsoft TTS system."""


class AparsoftTTSError(Exception):
    """Base exception for all Aparsoft TTS errors."""

    pass


class ConfigurationError(AparsoftTTSError):
    """Raised when there's a configuration error."""

    pass


class AudioProcessingError(AparsoftTTSError):
    """Raised when audio processing fails."""

    pass


class TTSGenerationError(AparsoftTTSError):
    """Raised when TTS generation fails."""

    pass


class ModelLoadError(AparsoftTTSError):
    """Raised when model loading fails."""

    pass


class InvalidVoiceError(AparsoftTTSError):
    """Raised when an invalid voice is specified."""

    pass


class InvalidParameterError(AparsoftTTSError):
    """Raised when invalid parameters are provided."""

    pass


class FileOperationError(AparsoftTTSError):
    """Raised when file operations fail."""

    pass


class MCPServerError(AparsoftTTSError):
    """Raised when MCP server operations fail."""

    pass
