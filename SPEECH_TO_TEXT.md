# Speech-to-Text

## Overview

Transcribe audio files to text using OpenAI Whisper. Supports 99+ languages with automatic detection.

## Features

- 99+ language support with automatic detection
- Translation to English from any language
- Multiple model sizes (tiny to large)
- Timestamped transcription segments
- Handles background noise and accents
- Supports WAV, MP3, MP4, MPEG, MPGA, M4A, WEBM

## Installation

```bash
# Install package
pip install -e ".[stt]"

# Install FFmpeg (required)
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS
# Windows: Download from https://ffmpeg.org/download.html
```

## Usage

### 1. Python API

```python
from aparsoft_tts.utils.audio import transcribe_audio

# Basic transcription
result = transcribe_audio("interview.wav")
print(result['text'])

# Save to file
result = transcribe_audio(
    audio_path="meeting.wav",
    output_path="meeting_transcript.txt",
    model_size="base"  # Options: tiny, base, small, medium, large
)

# Transcribe with language hint
result = transcribe_audio(
    audio_path="french_speech.wav",
    language="fr",  # ISO language code
    model_size="medium"
)

# Translate to English
result = transcribe_audio(
    audio_path="spanish_interview.mp3",
    task="translate",  # Translates to English
    model_size="small"
)

# Access detailed results
print(f"Text: {result['text']}")
print(f"Language: {result['language']}")
print(f"Segments: {len(result['segments'])}")

# Iterate through timestamped segments
for segment in result['segments']:
    start = segment['start']
    end = segment['end']
    text = segment['text']
    print(f"[{start:.2f}s -> {end:.2f}s]: {text}")
```

### 2. MCP Tool (Claude Desktop / Cursor)

```
"Transcribe this audio file: /path/to/interview.wav"
"Convert speech.mp3 to text with medium model"
"Translate french_audio.wav to English"
```

## Whisper Model Sizes

Choose the right model based on your speed/accuracy requirements:

| Model | Size | RAM | Speed | Accuracy | Best For |
|-------|------|-----|-------|----------|----------|
| `tiny` | 39M | ~1GB | Fastest | Basic | Quick drafts, testing |
| `base` | 74M | ~1GB | Fast | Good | **Default choice** |
| `small` | 244M | ~2GB | Moderate | Better | Balanced use |
| `medium` | 769M | ~5GB | Slower | High | Professional transcription |
| `large` | 1550M | ~10GB | Slowest | Best | Maximum accuracy needed |

**Recommendation**: Start with `base` (default) — it offers excellent accuracy for most use cases while being fast.

## Language Support

Supports 99 languages: English, Spanish, French, German, Italian, Portuguese, Russian, Japanese, Chinese, Korean, Arabic, Hindi, and more.

Leave `language` parameter empty for automatic detection.

## Examples

### Example 1: Basic Transcription

```python
from aparsoft_tts.utils.audio import transcribe_audio

result = transcribe_audio(
    audio_path="audio.mp3",
    output_path="transcript.txt",
    model_size="base"
)

print(result['text'])
print(f"Language: {result['language']}")
```

### Example 2: Timestamped Transcription

```python
result = transcribe_audio("meeting.wav", model_size="medium")

for segment in result['segments']:
    print(f"[{segment['start']:.1f}s] {segment['text']}")
```

### Example 3: Translation to English

```python
result = transcribe_audio(
    audio_path="spanish_podcast.mp3",
    task="translate"  # Translates to English
)

print(result['text'])
```

### Example 4: Batch Transcription

```python
from pathlib import Path

for audio_file in Path("interviews/").glob("*.wav"):
    output_file = audio_file.with_suffix(".txt")
    result = transcribe_audio(audio_file, output_file)
    print(f"✓ {audio_file.name}")
```

### Example 5: Multi-Voice Podcast + Transcription

```python
from aparsoft_tts import TTSEngine
from aparsoft_tts.utils.audio import combine_audio_segments, save_audio

# Generate multi-voice podcast
engine = TTSEngine()
segments = [
    {"text": "Welcome to the show!", "voice": "am_michael"},
    {"text": "Great to be here.", "voice": "af_sarah"},
]

audio_segments = []
for seg in segments:
    audio = engine.generate(seg["text"], voice=seg["voice"])
    audio_segments.append(audio)

combined = combine_audio_segments(audio_segments, gap_duration=0.6)
save_audio(combined, "podcast.wav")

# Transcribe the podcast
result = transcribe_audio("podcast.wav", "podcast_transcript.txt")
print(result['text'])
```

## Return Value Structure

The `transcribe_audio()` function returns a dictionary:

```python
{
    'text': str,           # Full transcription text
    'language': str,       # Detected/specified language code
    'segments': [          # List of timestamped segments
        {
            'id': int,           # Segment number
            'start': float,      # Start time in seconds
            'end': float,        # End time in seconds
            'text': str,         # Segment text
            'tokens': list,      # Token IDs
            'temperature': float,
            'avg_logprob': float,
            'compression_ratio': float,
            'no_speech_prob': float
        },
        ...
    ]
}
```

## Performance Tips

- Start with `base` model for most use cases
- Use `tiny` for quick testing
- Use `medium` or `large` for production
- Specify language if known (faster than auto-detect)
- Clean audio improves accuracy

## Troubleshooting

**ImportError**: `pip install openai-whisper`

**FFmpeg not found**: `sudo apt-get install ffmpeg` (Ubuntu) or `brew install ffmpeg` (macOS)

**Slow transcription**: Use smaller model (`base` or `tiny`)

**Poor accuracy**: Use larger model (`medium` or `large`)

**Out of memory**: Use smaller model or shorter clips

## Integration Examples

```python
# Verify TTS output
engine = TTSEngine()
engine.generate("Hello world", "output.wav")
result = transcribe_audio("output.wav")
print(result['text'])  # "Hello world"
```

## API Reference

### `transcribe_audio()`

```python
def transcribe_audio(
    audio_path: Path | str,
    output_path: Path | str | None = None,
    model_size: str = "base",
    language: str | None = None,
    task: str = "transcribe",
) -> dict:
```

**Parameters:**
- `audio_path`: Path to audio file
- `output_path`: Optional output text file path
- `model_size`: Whisper model size (tiny/base/small/medium/large)
- `language`: ISO language code (e.g., 'en', 'es') or None for auto-detect
- `task`: "transcribe" (same language) or "translate" (to English)

**Returns:**
- Dictionary with 'text', 'language', and 'segments'

**Raises:**
- `ImportError`: If openai-whisper not installed
- `AudioProcessingError`: If transcription fails
- `FileNotFoundError`: If audio file not found

## License

Apache 2.0 (same as the main project). OpenAI Whisper is MIT License.

## Support

- GitHub Issues: https://github.com/aparsoft/kokoro-youtube-tts/issues
- Email: contact@aparsoft.com
