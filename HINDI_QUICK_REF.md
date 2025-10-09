# 🇮🇳 Hindi TTS Quick Reference

## Hindi Voices

| Voice | Type | Gender | Quality | Usage |
|-------|------|--------|---------|-------|
| `hf_alpha` | Hindi | Female | Grade C | General female voice |
| `hf_beta` | Hindi | Female | Grade C | Alternative female voice |
| `hm_omega` | Hindi | Male | Grade C | General male voice |
| `hm_psi` | Hindi | Male | Grade C | Alternative male voice |

## Quick Start

```python
from aparsoft_tts.core.engine import TTSEngine

engine = TTSEngine()

# Generate Hindi speech
engine.generate(
    text="नमस्ते दुनिया",
    output_path="output.wav",
    voice="hf_alpha"  # Use any Hindi voice
)
```

## Language Code

- **Automatic**: Hindi voices (hf_*, hm_*) automatically use `lang_code='h'`
- **Manual**: Not needed - engine detects from voice prefix

## Prerequisites

```bash
# Install espeak-ng for Hindi support
sudo apt-get install espeak-ng  # Linux
brew install espeak-ng          # macOS
```

## MCP Tools

### Generate Speech
```python
await generate_speech(GenerateSpeechRequest(
    text="नमस्ते",
    voice="hf_alpha",
    output_file="hindi.wav"
))
```

### Batch Generate
```python
await batch_generate(BatchGenerateRequest(
    texts=["पहला", "दूसरा", "तीसरा"],
    voice="hm_omega",
    output_dir="hindi_batch/"
))
```

### Process Script
```python
await process_script(ProcessScriptRequest(
    script_path="hindi_script.txt",
    voice="hf_beta",
    output_path="hindi_audio.wav"
))
```

### Hindi Podcast
```python
await generate_podcast(GeneratePodcastRequest(
    segments=[
        PodcastSegment(text="होस्ट का परिचय", voice="hf_alpha"),
        PodcastSegment(text="अतिथि का जवाब", voice="hm_omega"),
    ],
    output_path="hindi_podcast.wav"
))
```

## Speed Guide

| Speed | Use Case |
|-------|----------|
| 0.8-0.9 | Clear narration, educational content |
| 1.0 | Normal speech, general use |
| 1.1-1.2 | Excitement, dynamic content |

## Common Issues

**Issue**: "espeak-ng not found"  
**Fix**: `sudo apt-get install espeak-ng`

**Issue**: Poor audio quality  
**Fix**: Use `enhance=True` and speed=0.9-1.0

**Issue**: Text sounds wrong  
**Fix**: Ensure text is in Devanagari (not romanized)

## Best Practices

1. ✅ Use Devanagari script (नमस्ते)
2. ✅ Enable audio enhancement
3. ✅ Keep chunks 100-250 tokens
4. ✅ Use speed 0.9-1.1 for clarity
5. ❌ Don't mix Hindi/English in same generation

## Testing

Run the test suite:
```bash
python test_hindi_tts.py
```

## Support

See `HINDI_SUPPORT.md` for complete documentation.
