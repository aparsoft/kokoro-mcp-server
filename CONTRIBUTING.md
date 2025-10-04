# Contributing to Aparsoft TTS

Thank you for your interest in contributing to Aparsoft TTS! This document provides guidelines and instructions for contributing.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/aparsoft/youtube-tts.git
cd youtube-tts
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install in development mode with all optional dependencies
pip install -e ".[dev,mcp,cli,all]"

# Install pre-commit hooks
pre-commit install
```

### 4. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get install espeak-ng ffmpeg libsndfile1
```

**macOS:**
```bash
brew install espeak ffmpeg
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Write clear, documented code
- Follow the existing code style
- Add tests for new features
- Update documentation as needed

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aparsoft_tts

# Run specific test file
pytest tests/unit/test_engine.py

# Run with verbose output
pytest -v
```

### 4. Code Quality Checks

```bash
# Format code with Black
black .

# Lint with Ruff
ruff check .

# Type check with mypy
mypy aparsoft_tts/
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
# or
git commit -m "fix: resolve bug in audio processing"
```

Use conventional commit messages:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style Guidelines

### Python Style

- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints where appropriate
- Write descriptive docstrings (Google style)

### Example:

```python
def process_audio(
    audio: NDArray[np.float32],
    sample_rate: int = 24000,
    enhance: bool = True,
) -> NDArray[np.float32]:
    """Process audio with enhancement.

    Args:
        audio: Input audio array
        sample_rate: Sample rate in Hz
        enhance: Apply enhancement

    Returns:
        Processed audio array

    Raises:
        AudioProcessingError: If processing fails

    Example:
        >>> audio = np.random.randn(24000)
        >>> processed = process_audio(audio)
    """
    pass
```

### Logging

Use structured logging with appropriate log levels:

```python
from aparsoft_tts.utils.logging import get_logger

log = get_logger(__name__)

log.info("processing_started", file="audio.wav", size=12345)
log.error("processing_failed", error=str(e))
```

### Error Handling

Use custom exceptions and provide context:

```python
from aparsoft_tts.utils.exceptions import AudioProcessingError

try:
    result = process_audio(audio)
except Exception as e:
    log.error("processing_failed", error=str(e))
    raise AudioProcessingError(f"Failed to process audio: {e}") from e
```

## Testing Guidelines

### Unit Tests

- Test individual functions and methods
- Use mocks for external dependencies
- Aim for >80% code coverage

### Integration Tests

- Test complete workflows
- Test actual TTS generation (may be slow)
- Mark slow tests with `@pytest.mark.slow`

### Example Test:

```python
import pytest
from aparsoft_tts import TTSEngine

def test_generate_audio(tmp_path):
    """Test audio generation."""
    engine = TTSEngine()
    output = tmp_path / "test.wav"

    result = engine.generate("Hello", output_path=output)

    assert output.exists()
    assert output.stat().st_size > 0
```

## Documentation

### Docstrings

- Use Google-style docstrings
- Include examples where helpful
- Document all parameters and return values
- List possible exceptions

### README Updates

Update README.md if you:
- Add new features
- Change installation steps
- Modify usage examples
- Update dependencies

## Pull Request Process

1. **Ensure CI passes**: All tests, linting, and type checks must pass
2. **Update documentation**: Add/update relevant documentation
3. **Add tests**: Include tests for new features
4. **Update CHANGELOG**: Add entry describing your changes
5. **Request review**: Wait for maintainer review
6. **Address feedback**: Make requested changes
7. **Merge**: Maintainer will merge after approval

## Reporting Issues

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version)
- Relevant logs/error messages

### Feature Requests

Include:
- Clear description of the feature
- Use case/motivation
- Proposed implementation (optional)
- Examples of similar features elsewhere (optional)

## Questions?

- Open an issue for questions
- Email: contact@aparsoft.com
- Website: https://aparsoft.com

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to Aparsoft TTS! 🎙️
