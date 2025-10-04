"""Unit tests for audio utilities."""

import numpy as np
import pytest
from pathlib import Path

from aparsoft_tts.utils.audio import (
    enhance_audio,
    combine_audio_segments,
    save_audio,
    load_audio,
    chunk_audio,
    get_audio_duration,
)
from aparsoft_tts.utils.exceptions import AudioProcessingError


class TestAudioUtilities:
    """Tests for audio utility functions."""

    def test_enhance_audio(self):
        """Test audio enhancement."""
        # Create test audio
        audio = np.random.randn(24000).astype(np.float32)
        enhanced = enhance_audio(audio, sample_rate=24000)

        assert isinstance(enhanced, np.ndarray)
        assert enhanced.dtype == np.float32
        assert len(enhanced) <= len(audio)  # May be trimmed

    def test_enhance_audio_no_trim(self):
        """Test enhancement without trimming."""
        audio = np.random.randn(24000).astype(np.float32)
        enhanced = enhance_audio(audio, trim_silence=False)

        assert len(enhanced) == len(audio)

    def test_combine_audio_segments(self):
        """Test combining audio segments."""
        seg1 = np.random.randn(1000).astype(np.float32)
        seg2 = np.random.randn(1000).astype(np.float32)
        seg3 = np.random.randn(1000).astype(np.float32)

        combined = combine_audio_segments([seg1, seg2, seg3], gap_duration=0.1)

        assert isinstance(combined, np.ndarray)
        assert len(combined) > len(seg1) + len(seg2) + len(seg3)  # Includes gaps

    def test_combine_empty_segments(self):
        """Test combining empty segments raises error."""
        with pytest.raises(AudioProcessingError):
            combine_audio_segments([])

    def test_save_and_load_audio(self, tmp_path):
        """Test saving and loading audio."""
        audio = np.random.randn(24000).astype(np.float32)
        output_path = tmp_path / "test.wav"

        # Save
        saved_path = save_audio(audio, output_path)
        assert saved_path.exists()

        # Load
        loaded_audio, sr = load_audio(saved_path)
        assert isinstance(loaded_audio, np.ndarray)
        assert sr == 24000
        assert len(loaded_audio) > 0

    def test_chunk_audio(self):
        """Test chunking audio."""
        audio = np.random.randn(10000).astype(np.float32)
        chunks = chunk_audio(audio, chunk_size=1024)

        assert len(chunks) > 0
        assert all(isinstance(chunk, np.ndarray) for chunk in chunks)

    def test_get_audio_duration(self):
        """Test getting audio duration."""
        audio = np.random.randn(24000).astype(np.float32)  # 1 second at 24kHz
        duration = get_audio_duration(audio, sample_rate=24000)

        assert duration == pytest.approx(1.0, rel=0.01)
