"""Pytest configuration and fixtures."""

import pytest
import numpy as np
from pathlib import Path


@pytest.fixture
def sample_audio():
    """Generate sample audio data for testing."""
    return np.random.randn(24000).astype(np.float32)


@pytest.fixture
def sample_text():
    """Provide sample text for TTS testing."""
    return "This is a test sentence for text-to-speech conversion."


@pytest.fixture
def test_output_dir(tmp_path):
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir
