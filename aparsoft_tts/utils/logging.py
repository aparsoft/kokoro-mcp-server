# aparsoft_tts/utils/logging.py

"""Structured logging configuration using structlog."""

import logging
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.types import FilteringBoundLogger, Processor

from aparsoft_tts.config import LoggingConfig


def add_correlation_id(
    logger: FilteringBoundLogger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add correlation ID to log entries for request tracing.

    Args:
        logger: The bound logger instance
        method_name: The name of the method being called
        event_dict: The event dictionary

    Returns:
        Updated event dictionary with correlation ID
    """
    # Try to get correlation ID from context
    correlation_id = structlog.contextvars.get_contextvars().get("correlation_id")
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def add_service_context(
    logger: FilteringBoundLogger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add service context information to logs.

    Args:
        logger: The bound logger instance
        method_name: The name of the method being called
        event_dict: The event dictionary

    Returns:
        Updated event dictionary with service context
    """
    event_dict.setdefault("service", "aparsoft-tts")
    event_dict.setdefault("version", "1.0.0")
    return event_dict


def setup_logging(config: LoggingConfig | None = None) -> None:
    """Configure structured logging for the application.

    This function sets up structlog with Comprehensive configuration including:
    - Structured JSON logging for production
    - Human-readable console logging for development
    - Correlation IDs for request tracing
    - Context management
    - Performance-optimized processing chain

    Args:
        config: Logging configuration. If None, uses default config.

    Example:
        >>> from aparsoft_tts.utils.logging import setup_logging
        >>> setup_logging()
        >>> log = structlog.get_logger()
        >>> log.info("application_started", version="1.0.0")
    """
    if config is None:
        from aparsoft_tts.config import get_config

        config = get_config().logging

    # Ensure log directory exists
    if config.output in ("file", "both"):
        config.log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard library logging
    # For MCP compatibility: suppress stdlib logging to avoid JSON parsing errors
    # Only structlog messages should go to stderr in JSON format
    if config.output in ("stdout", "stderr"):
        # Disable stdlib logging handlers to prevent non-JSON output
        logging.root.handlers.clear()
        # Set high level to suppress unwanted logs
        logging.basicConfig(
            format="%(message)s",
            level=logging.CRITICAL + 1,  # Suppress all stdlib logs
            handlers=[],  # No handlers
        )
    else:
        # File-only logging can use normal format
        logging.basicConfig(
            format="%(message)s",
            level=getattr(logging, config.level),
        )

    # Add file handler if needed
    if config.output in ("file", "both"):
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setLevel(getattr(logging, config.level))
        logging.root.addHandler(file_handler)

    # Build processor chain
    processors: list[Processor] = [
        # Add correlation ID and service context
        add_correlation_id,
        add_service_context,
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
    ]

    # Add timestamp if configured
    if config.include_timestamp:
        processors.append(structlog.processors.TimeStamper(fmt="iso"))

    # Add caller info if configured
    if config.include_caller:
        processors.append(structlog.processors.CallsiteParameterAdder())

    # Add exception info
    processors.append(structlog.processors.StackInfoRenderer())
    processors.append(structlog.processors.ExceptionRenderer())

    # Choose renderer based on format
    if config.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Disable colors for stderr output (MCP compatibility)
        use_colors = config.output == "stdout"
        processors.append(structlog.dev.ConsoleRenderer(colors=use_colors))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, config.level)),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> FilteringBoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name. If None, uses calling module name.

    Returns:
        Configured structlog logger

    Example:
        >>> log = get_logger(__name__)
        >>> log.info("processing_started", file="audio.wav")
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """Bind context variables that will be included in all subsequent log entries.

    Args:
        **kwargs: Key-value pairs to bind to logger context

    Example:
        >>> bind_context(correlation_id="abc-123", user_id="user-456")
        >>> log = get_logger()
        >>> log.info("request_processed")  # Will include correlation_id and user_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*keys: str) -> None:
    """Unbind context variables.

    Args:
        *keys: Keys to unbind from context

    Example:
        >>> unbind_context("correlation_id", "user_id")
    """
    structlog.contextvars.unbind_contextvars(*keys)


def clear_context() -> None:
    """Clear all context variables.

    Example:
        >>> clear_context()
    """
    structlog.contextvars.clear_contextvars()


class LoggerMixin:
    """Mixin class to add logging capabilities to any class.

    Example:
        >>> class MyService(LoggerMixin):
        ...     def process(self):
        ...         self.log.info("processing", item="data")
    """

    @property
    def log(self) -> FilteringBoundLogger:
        """Get logger bound to this class.

        Returns:
            Bound logger instance
        """
        if not hasattr(self, "_log"):
            self._log = get_logger(self.__class__.__name__)
        return self._log
