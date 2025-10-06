# Speech-to-Text Quick Reference

## Installation

```bash
# Install STT support
pip install -e ".[stt]"

# Or complete installation (TTS + STT + MCP + CLI + Streamlit)
pip install -e ".[complete]"

# Install system dependency (required)
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS
```

## Basic Usage

```python
from aparsoft_tts.utils.audio import transcribe_audio

# Simple transcription
result = transcribe_audio("audio.wav")
print(result['text'])

# Save to file
transcribe_audio("audio.wav", output_path="transcript.txt")

# Choose model size
transcribe_audio("audio.wav", model_size="medium")  # tiny/base/small/medium/large

# Specify language
transcribe_audio("audio.wav", language="en")

# Translate to English
transcribe_audio("french.wav", task="translate")
```

## MCP Usage (Claude Desktop)

```
"Transcribe interview.wav"
"Convert speech.mp3 to text with medium model"
"Translate spanish_audio.wav to English"
```

## Model Sizes

| Model | Size | RAM | Best For |
|-------|------|-----|----------|
| tiny | 39M | 1GB | Testing |
| base | 74M | 1GB | **Default** |
| small | 244M | 2GB | Balanced |
| medium | 769M | 5GB | Professional |
| large | 1550M | 10GB | Max accuracy |

## Common Languages

```python
# English
transcribe_audio("audio.wav", language="en")

# Spanish
transcribe_audio("audio.wav", language="es")

# French
transcribe_audio("audio.wav", language="fr")

# Auto-detect (leave empty)
transcribe_audio("audio.wav")
```

## Return Format

```python
{
    'text': 'Full transcription...',
    'language': 'en',
    'segments': [
        {
            'start': 0.0,
            'end': 5.2,
            'text': 'First sentence.'
        },
        ...
    ]
}
```

## Complete Example

```python
from aparsoft_tts.utils.audio import transcribe_audio

# Transcribe with all options
result = transcribe_audio(
    audio_path="meeting.wav",
    output_path="meeting_transcript.txt",
    model_size="medium",
    language="en",
    task="transcribe"
)

# Print results
print(f"Transcribed {len(result['text'])} characters")
print(f"Language: {result['language']}")
print(f"Segments: {len(result['segments'])}")

# Access timestamped segments
for segment in result['segments']:
    print(f"[{segment['start']:.1f}s] {segment['text']}")
```

## Multi-Voice Podcast Example

```python
from aparsoft_tts import TTSEngine
from aparsoft_tts.utils.audio import combine_audio_segments, save_audio, transcribe_audio

# Generate podcast with different voices
engine = TTSEngine()
segments = [
    {"text": "Welcome listeners!", "voice": "am_michael"},
    {"text": "Thanks for having me.", "voice": "af_sarah"},
]

audio_segs = [engine.generate(s["text"], voice=s["voice"]) for s in segments]
combined = combine_audio_segments(audio_segs, gap_duration=0.6)
save_audio(combined, "podcast.wav")

# Transcribe the podcast
result = transcribe_audio("podcast.wav", "transcript.txt")
print(result['text'])
```

## Troubleshooting

### ImportError
```bash
pip install openai-whisper
```

### FFmpeg not found
```bash
sudo apt-get install ffmpeg  # Ubuntu
brew install ffmpeg          # macOS
```

### Slow transcription
Use smaller model: `model_size="base"` or `model_size="tiny"`

### Poor accuracy
Use larger model: `model_size="medium"` or `model_size="large"`

### Out of memory
Use smaller model or process shorter clips

## Full Documentation

See [SPEECH_TO_TEXT.md](SPEECH_TO_TEXT.md) for complete documentation.
