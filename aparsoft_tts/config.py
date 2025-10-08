# aparsoft_tts/config.py

"""Configuration management for Aparsoft TTS system."""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TTSConfig(BaseSettings):
    """TTS engine configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TTS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Voice Settings
    voice: str = Field(
        default="am_michael",
        description="Default voice to use (am_michael, bm_george, am_adam, af_bella, etc.)",
    )
    # DEPRECATED: lang_code is now automatically determined from voice prefix
    # This field is kept for backwards compatibility but is not used by the engine
    lang_code: Literal["a", "b"] = Field(
        default="a",
        description="Language code auto-detected from voice prefix (am_/af_='a', bm_/bf_='b')",
    )
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed (0.5-2.0)")
    repo_id: str = Field(
        default="hexgrad/Kokoro-82M", description="Hugging Face model repository ID"
    )

    # Audio Processing
    sample_rate: int = Field(default=24000, description="Audio sample rate in Hz")
    enhance_audio: bool = Field(
        default=True, description="Apply audio enhancement (normalization, trimming, etc.)"
    )
    trim_silence: bool = Field(default=True, description="Trim silence from audio")
    trim_db: float = Field(
        default=30.0,
        description="dB threshold for silence trimming (higher = less aggressive, better preserves soft endings)",
    )
    fade_duration: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Fade in/out duration in seconds"
    )

    # Podcast-specific settings
    podcast_default_gap: float = Field(
        default=0.6,
        ge=0.0,
        le=5.0,
        description="Default gap between podcast segments in seconds",
    )
    podcast_crossfade_duration: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Crossfade duration between podcast segments in seconds",
    )
    podcast_max_segments: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of segments allowed in a podcast",
    )

    # Token Limits (Kokoro-82M constraints)
    # Based on: https://github.com/remsky/Kokoro-FastAPI
    # Kokoro can process up to 510 tokens, but quality degrades >400 tokens
    token_target_min: int = Field(
        default=100, ge=20, le=500, description="Minimum tokens per chunk (avoid very short chunks)"
    )
    token_target_max: int = Field(
        default=250,
        ge=100,
        le=400,
        description="Target maximum tokens per chunk (optimal quality range)",
    )
    token_absolute_max: int = Field(
        default=450,
        ge=250,
        le=510,
        description="Absolute maximum tokens (hard limit before rushed speech)",
    )
    chunk_gap_duration: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Gap duration between auto-generated chunks in seconds",
    )

    # Output Settings
    output_dir: Path = Field(
        default=Path("outputs"), description="Default output directory for generated audio"
    )
    output_format: Literal["wav", "flac", "mp3"] = Field(
        default="wav", description="Output audio format"
    )

    # Performance
    chunk_size: int = Field(
        default=1024, gt=0, description="Audio chunk size for streaming/processing"
    )
    max_workers: int = Field(
        default=4, ge=1, le=32, description="Maximum worker threads for parallel processing"
    )

    @field_validator("output_dir", mode="before")
    @classmethod
    def create_output_dir(cls, v: Path | str) -> Path:
        """Ensure output directory exists."""
        path = Path(v) if isinstance(v, str) else v
        path.mkdir(parents=True, exist_ok=True)
        return path


class MCPConfig(BaseSettings):
    """MCP server configuration."""

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server Settings
    server_name: str = Field(default="aparsoft-tts-server", description="MCP server name")
    server_version: str = Field(default="1.0.0", description="MCP server version")

    # Transport
    transport: Literal["stdio", "http", "sse"] = Field(
        default="stdio", description="Transport mechanism"
    )
    host: str = Field(default="localhost", description="Host for HTTP/SSE transport")
    port: int = Field(default=8000, ge=1024, le=65535, description="Port for HTTP/SSE transport")

    # Rate Limiting
    enable_rate_limiting: bool = Field(
        default=True, description="Enable rate limiting for API calls"
    )
    rate_limit_calls: int = Field(default=100, description="Max calls per time window")
    rate_limit_period: int = Field(default=60, description="Time window in seconds")


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Log Level
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # Output
    format: Literal["json", "console"] = Field(default="console", description="Log output format")
    output: Literal["stdout", "stderr", "file", "both"] = Field(
        default="stdout", description="Log output destination"
    )
    log_file: Path = Field(default=Path("logs/aparsoft_tts.log"), description="Log file path")

    # Structured Logging
    include_timestamp: bool = Field(default=True, description="Include timestamp in logs")
    include_caller: bool = Field(default=True, description="Include caller info in logs")
    include_context: bool = Field(
        default=True, description="Include contextual information in logs"
    )

    @field_validator("log_file", mode="before")
    @classmethod
    def create_log_dir(cls, v: Path | str) -> Path:
        """Ensure log directory exists."""
        path = Path(v) if isinstance(v, str) else v
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


class Config(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Environment
    environment: Literal["development", "staging", "production"] = Field(
        default="production", description="Application environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # Engine Selection
    engine: Literal["kokoro", "openvoice"] = Field(
        default="kokoro",
        description="TTS engine to use: 'kokoro' (fast, English) or 'openvoice' (cloning, multilingual)"
    )

    # Sub-configurations
    tts: TTSConfig = Field(default_factory=TTSConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get global configuration instance.

    Returns:
        Config: Global configuration object

    Example:
        >>> config = get_config()
        >>> print(config.tts.voice)
        am_michael
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment/file.

    Returns:
        Config: Reloaded configuration object
    """
    global _config
    _config = Config()
    return _config
