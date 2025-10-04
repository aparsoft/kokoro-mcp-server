"""Unit tests for TTS engine."""

import numpy as np
import pytest
from pathlib import Path

from aparsoft_tts.core.engine import TTSEngine, ALL_VOICES
from aparsoft_tts.config import TTSConfig
from aparsoft_tts.utils.exceptions import (
    InvalidVoiceError,
    InvalidParameterError,
    TTSGenerationError,
)


@pytest.fixture
def engine():
    """Create a TTS engine instance for testing."""
    config = TTSConfig(enhance_audio=False)  # Disable enhancement for faster tests
    return TTSEngine(config=config)


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir


class TestTTSEngine:
    """Tests for TTSEngine class."""

    def test_initialization(self, engine):
        """Test engine initializes correctly."""
        assert engine is not None
        assert engine.pipeline is not None
        assert engine.config is not None

    def test_list_voices(self):
        """Test listing available voices."""
        voices = TTSEngine.list_voices()
        assert "male" in voices
        assert "female" in voices
        assert len(voices["male"]) > 0
        assert len(voices["female"]) > 0
        assert "am_michael" in voices["male"]

    def test_generate_audio_array(self, engine):
        """Test generating audio returns numpy array when no output path."""
        audio = engine.generate("Hello world")
        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0
        assert audio.dtype == np.float32

    def test_generate_with_file_output(self, engine, temp_output_dir):
        """Test generating audio saves to file."""
        output_path = temp_output_dir / "test.wav"
        result = engine.generate("Hello world", output_path=output_path)

        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_generate_with_different_voice(self, engine):
        """Test generating with different voice."""
        audio = engine.generate("Hello", voice="am_adam")
        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0

    def test_generate_with_speed(self, engine):
        """Test generating with different speed."""
        audio = engine.generate("Hello", speed=1.5)
        assert isinstance(audio, np.ndarray)

    def test_generate_invalid_voice(self, engine):
        """Test that invalid voice raises error."""
        with pytest.raises(InvalidVoiceError):
            engine.generate("Hello", voice="invalid_voice")

    def test_generate_invalid_speed(self, engine):
        """Test that invalid speed raises error."""
        with pytest.raises(InvalidParameterError):
            engine.generate("Hello", speed=3.0)

    def test_batch_generate(self, engine, temp_output_dir):
        """Test batch generation."""
        texts = ["First", "Second", "Third"]
        paths = engine.batch_generate(texts, output_dir=temp_output_dir)

        assert len(paths) == 3
        for path in paths:
            assert path.exists()
            assert path.stat().st_size > 0

    def test_process_script(self, engine, temp_output_dir, tmp_path):
        """Test processing a script file."""
        # Create test script
        script_path = tmp_path / "test_script.txt"
        script_path.write_text("""
First paragraph.

Second paragraph.

Third paragraph.
        """.strip())

        output_path = temp_output_dir / "output.wav"
        result = engine.process_script(script_path, output_path)

        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_process_script_nonexistent_file(self, engine, temp_output_dir):
        """Test processing nonexistent script raises error."""
        with pytest.raises(FileNotFoundError):
            engine.process_script("nonexistent.txt", temp_output_dir / "output.wav")
