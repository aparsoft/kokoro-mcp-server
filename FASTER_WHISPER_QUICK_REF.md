# faster-whisper Quick Reference Guide

## 🚀 Quick Start

### Installation
```bash
pip install faster-whisper

# Pre-download models for later (optional but smart!)
python scripts/preload_whisper_models.py
```

### Basic Usage
```python
from aparsoft_tts.utils.audio import transcribe_audio

# Simple transcription (uses faster-whisper by default)
result = transcribe_audio("audio.wav")
print(result['text'])
```

---

## 📋 Common Use Cases

### 1. Fast Transcription (CPU)
```python
result = transcribe_audio(
    "audio.wav",
    model_size="base",
    device="cpu",
    compute_type="int8"  # Fastest on CPU
)
```

### 2. High Accuracy (GPU)
```python
result = transcribe_audio(
    "audio.wav",
    model_size="large-v3",
    device="cuda",
    compute_type="float16",
    beam_size=10
)
```

### 3. Word-Level Timestamps
```python
result = transcribe_audio(
    "audio.wav",
    word_timestamps=True
)

for seg in result['segments']:
    for word in seg.get('words', []):
        print(f"[{word['start']:.2f}s] {word['word']}")
```

### 4. Multiple Languages
```python
# Auto-detect language
result = transcribe_audio("audio.wav")

# Specify language
result = transcribe_audio("audio.wav", language="es")

# Translate to English
result = transcribe_audio("audio.wav", task="translate")
```

### 5. Remove Silence (VAD)
```python
result = transcribe_audio(
    "audio.wav",
    vad_filter=True  # Removes silence automatically
)
```

### 6. Save Transcript
```python
result = transcribe_audio(
    "audio.wav",
    output_path="transcript.txt"
)
```

---

## 🎯 Model Selection Guide

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny | 39M | ⚡⚡⚡ | ⭐⭐ | Real-time apps |
| base | 74M | ⚡⚡ | ⭐⭐⭐ | Balanced (default) |
| small | 244M | ⚡ | ⭐⭐⭐⭐ | Good quality |
| medium | 769M | 🐌 | ⭐⭐⭐⭐⭐ | High quality |
| large-v3 | 1550M | 🐌🐌 | ⭐⭐⭐⭐⭐ | Best quality |
| turbo | 809M | ⚡ | ⭐⭐⭐⭐⭐ | Fast + accurate |

**Recommendation:** Use **base** for general use, **turbo** for production, **large-v3** for critical accuracy.

---

## ⚙️ Parameters Reference

### device
- `"auto"` - Auto-select (default)
- `"cpu"` - Use CPU
- `"cuda"` - Use GPU

### compute_type
- `"default"` - Auto-select (default)
- `"int8"` - Fastest on CPU, low memory
- `"float16"` - Best for GPU
- `"float32"` - Highest precision

### beam_size
- `1` - Fastest, greedy decoding
- `5` - Balanced (default)
- `10+` - Most accurate, slower

### vad_filter
- `True` - Remove silence (default)
- `False` - Keep all audio

---

## 🧪 Testing Streaming

### Quick Test
```bash
python examples/test_streaming.py
```

### Verify in Code
```python
from aparsoft_tts import TTSEngine

engine = TTSEngine()
text = "Your long text here..."

# This should print progress
for i, chunk in enumerate(engine.generate_stream(text), 1):
    print(f"Chunk {i}: {len(chunk)} samples")
```

---

## 🔍 Result Format

```python
result = {
    'text': 'Full transcription text',
    'language': 'en',
    'language_probability': 0.98,
    'segments': [
        {
            'id': 0,
            'start': 0.0,
            'end': 2.5,
            'text': 'First sentence',
            'words': [  # If word_timestamps=True
                {
                    'start': 0.0,
                    'end': 0.5,
                    'word': 'First',
                    'probability': 0.95
                },
                # ...
            ]
        },
        # ...
    ]
}
```

---

## 💡 Performance Tips

### Fastest Setup
```python
result = transcribe_audio(
    "audio.wav",
    model_size="tiny",
    device="cuda",
    compute_type="int8_float16",
    beam_size=1
)
```

### Most Accurate Setup
```python
result = transcribe_audio(
    "audio.wav",
    model_size="large-v3",
    device="cuda",
    compute_type="float16",
    beam_size=10,
    word_timestamps=True
)
```

### Low Memory Setup
```python
result = transcribe_audio(
    "audio.wav",
    model_size="base",
    device="cpu",
    compute_type="int8"
)
```

---

## 🐛 Common Issues

### "CUDA not available"
```python
# Check if GPU is detected
from aparsoft_tts.utils.audio import _is_cuda_available
print(f"CUDA: {_is_cuda_available()}")

# If False, use CPU or install CUDA drivers
result = transcribe_audio("audio.wav", device="cpu")
```

### "Out of memory"
```python
# Use smaller model or int8
result = transcribe_audio(
    "audio.wav",
    model_size="base",  # or "tiny"
    compute_type="int8"
)
```

### "Too slow"
```python
# Use GPU if available, or smaller model
result = transcribe_audio(
    "audio.wav",
    model_size="tiny",
    device="cuda"  # if available
)
```

---

## 📊 Speed Comparison

**13 minutes of audio transcription:**

| Configuration | Time | Speed |
|--------------|------|-------|
| openai-whisper (GPU) | 2m 23s | 5.5x |
| faster-whisper (GPU, fp16) | 42s | ⚡ **18.6x** |
| faster-whisper (CPU, int8) | 1m 42s | 7.6x |
| faster-whisper (tiny, GPU) | 15s | ⚡ **52x** |

---

## 🎓 Examples

### Example 1: Transcribe YouTube Video
```python
# After downloading audio from YouTube
result = transcribe_audio(
    "youtube_video.mp3",
    output_path="transcript.txt",
    model_size="base",
    device="auto"
)
```

### Example 2: Transcribe Podcast
```python
result = transcribe_audio(
    "podcast.mp3",
    model_size="medium",
    vad_filter=True,  # Remove silence
    word_timestamps=True  # Get word timing
)
```

### Example 3: Batch Process Files
```python
import glob
from pathlib import Path

for audio_file in glob.glob("audio_files/*.wav"):
    output = Path(audio_file).with_suffix(".txt")
    transcribe_audio(audio_file, output_path=output)
```

### Example 4: Real-time Transcription
```python
# For live audio streams
result = transcribe_audio(
    "live_stream.wav",
    model_size="tiny",  # Fast
    device="cuda",
    beam_size=1  # Fastest
)
```

---

## 📚 Learn More

- Run examples: `python examples/speech_to_text_example.py`
- Test streaming: `python examples/test_streaming.py`
- Full docs: See `FASTER_WHISPER_IMPLEMENTATION.md`

---

**Quick Help:**
```python
# Check available parameters
help(transcribe_audio)

# List available voices
from aparsoft_tts import TTSEngine
voices = TTSEngine.list_voices()
```
