# 🇮🇳 Hindi Support in Aparsoft TTS

## Overview

Kokoro TTS now supports Hindi speech synthesis with 4 native Hindi voices. This guide explains how to use Hindi voices in your TTS projects.

## Available Hindi Voices

### Female Voices
- **`hf_alpha`** - Hindi female voice (alpha)
- **`hf_beta`** - Hindi female voice (beta)

### Male Voices
- **`hm_omega`** - Hindi male voice (omega)
- **`hm_psi`** - Hindi male voice (psi)

**Note**: All Hindi voices have Grade C quality with MM minutes (10-100 minutes) of training data. They use `lang_code='h'` which is automatically detected from the voice prefix.

## Prerequisites

### System Requirements
Hindi support requires `espeak-ng` with Hindi language support installed:

```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng

# macOS
brew install espeak-ng

# Windows
# Download and install from: https://github.com/espeak-ng/espeak-ng/releases
```

### Verify espeak-ng Hindi Support
```bash
# Test if Hindi is available
espeak-ng -v hi "नमस्ते" --stdout > test.wav
```

## Usage Examples

### Basic Usage

```python
from aparsoft_tts.core.engine import TTSEngine

# Initialize engine
engine = TTSEngine()

# Generate Hindi speech with female voice
engine.generate(
    text="नमस्ते, यह एक परीक्षण है।",
    output_path="hindi_output.wav",
    voice="hf_alpha"  # Automatically uses lang_code='h'
)

# Generate with male voice
engine.generate(
    text="मेरा नाम राज है।",
    output_path="hindi_male.wav",
    voice="hm_omega",
    speed=1.1
)
```

### Using Configuration

```python
from aparsoft_tts import TTSConfig
from aparsoft_tts.core.engine import TTSEngine

# Set Hindi as default voice
config = TTSConfig(
    voice="hf_alpha",
    speed=1.0,
    enhance_audio=True
)

engine = TTSEngine(config=config)

# Now all generations use Hindi by default
engine.generate(
    text="यह डिफ़ॉल्ट हिंदी आवाज़ है।",
    output_path="default_hindi.wav"
)
```

### Mixed Language Content (English + Hindi)

For content mixing English and Hindi, generate separate audio files and combine them:

```python
from aparsoft_tts.core.engine import TTSEngine
from aparsoft_tts.utils.audio import combine_audio_segments
import numpy as np

engine = TTSEngine()

# Generate English part
english_audio = engine.generate(
    text="Welcome to our channel.",
    voice="am_michael"
)

# Generate Hindi part
hindi_audio = engine.generate(
    text="आपका स्वागत है।",
    voice="hf_alpha"
)

# Combine with gap
combined = combine_audio_segments(
    segments=[english_audio, hindi_audio],
    sample_rate=24000,
    gap_duration=0.5
)

# Save combined audio
from aparsoft_tts.utils.audio import save_audio
save_audio(combined, "mixed_language.wav")
```

### Batch Processing for Hindi Content

```python
from aparsoft_tts.core.engine import TTSEngine

engine = TTSEngine()

# Multiple Hindi texts
hindi_texts = [
    "यह पहला वाक्य है।",
    "यह दूसरा वाक्य है।",
    "यह तीसरा वाक्य है।"
]

# Generate all with Hindi voice
paths = engine.batch_generate(
    texts=hindi_texts,
    output_dir="hindi_outputs/",
    voice="hf_beta",
    speed=1.0,
    filename_prefix="hindi"
)

print(f"Generated {len(paths)} audio files")
```

### Process Hindi Script File

```python
from aparsoft_tts.core.engine import TTSEngine

engine = TTSEngine()

# Process a complete Hindi script
# The script will be automatically chunked for optimal quality
result = engine.process_script(
    script_path="hindi_script.txt",
    output_path="hindi_voiceover.wav",
    voice="hm_psi",
    speed=1.0,
    gap_duration=0.5  # Gap between chunks
)

print(f"Hindi voiceover created: {result}")
```

## MCP Tool Integration

### Using aparsoft-tts:generate_speech

```python
# Through MCP tool
await generate_speech(GenerateSpeechRequest(
    text="नमस्ते दुनिया",
    voice="hf_alpha",
    speed=1.0,
    output_file="hindi_hello.wav",
    enhance=True
))
```

### Using aparsoft-tts:batch_generate

```python
# Batch generate Hindi audio files
await batch_generate(BatchGenerateRequest(
    texts=[
        "पहला वाक्य",
        "दूसरा वाक्य",
        "तीसरा वाक्य"
    ],
    voice="hm_omega",
    speed=1.0,
    output_dir="hindi_batch/"
))
```

### Using aparsoft-tts:process_script

```python
# Process complete Hindi script
await process_script(ProcessScriptRequest(
    script_path="my_hindi_script.txt",
    output_path="hindi_complete.wav",
    voice="hf_beta",
    speed=1.0,
    gap_duration=0.5
))
```

### Create Hindi Podcast

```python
# Multi-voice Hindi podcast with host and guest
await generate_podcast(GeneratePodcastRequest(
    segments=[
        PodcastSegment(
            text="इस पॉडकास्ट में आपका स्वागत है।",
            voice="hf_alpha",
            speed=1.0,
            name="host_intro"
        ),
        PodcastSegment(
            text="धन्यवाद। आज हम बात करेंगे...",
            voice="hm_omega",
            speed=1.05,
            name="guest_response"
        ),
        PodcastSegment(
            text="यह बहुत रोचक है।",
            voice="hf_alpha",
            speed=1.1,
            name="host_reaction"
        )
    ],
    output_path="hindi_podcast.wav",
    gap_duration=0.4
))
```

## Listing Available Voices

```python
from aparsoft_tts.core.engine import TTSEngine

# Get all voices
voices = TTSEngine.list_voices()

print("Hindi Male Voices:", voices['hindi_male'])
# Output: ['hm_omega', 'hm_psi']

print("Hindi Female Voices:", voices['hindi_female'])
# Output: ['hf_alpha', 'hf_beta']

print("All Voices:", voices['all'])
# Output: All available voices including English and Hindi
```

## Technical Details

### Automatic Language Detection

The engine automatically detects the language code from the voice prefix:

```python
from aparsoft_tts.core.engine import get_lang_code_from_voice

# These are handled automatically
print(get_lang_code_from_voice('hf_alpha'))   # Output: 'h'
print(get_lang_code_from_voice('hm_omega'))   # Output: 'h'
print(get_lang_code_from_voice('am_michael')) # Output: 'a'
```

### G2P (Grapheme-to-Phoneme)

Hindi voices use:
- **G2P Library**: `misaki[en]` (same as English)
- **Fallback**: `espeak-ng hi` for Hindi text
- **Phonemization**: Automatic conversion of Devanagari to IPA phonemes

### Token Limits

Same as English voices:
- **Optimal**: 100-250 tokens per chunk
- **Maximum**: 450 tokens (before rushed speech)
- **Hard limit**: 510 tokens (architectural maximum)

The engine automatically chunks Hindi text at sentence boundaries to maintain quality.

## Best Practices

### 1. Text Input
- Use proper Devanagari script (नमस्ते)
- Avoid mixing Hindi and English in the same generation
- Use proper punctuation for natural pausing

### 2. Speed Adjustment
```python
# Slower for clarity (recommended for Hindi)
engine.generate(text="...", voice="hf_alpha", speed=0.9)

# Normal speed
engine.generate(text="...", voice="hf_alpha", speed=1.0)

# Faster for excitement
engine.generate(text="...", voice="hf_alpha", speed=1.2)
```

### 3. Audio Enhancement
```python
# Enable enhancement for professional quality
config = TTSConfig(
    voice="hf_alpha",
    enhance_audio=True,
    trim_silence=True,
    trim_db=30.0,  # Conservative trimming
    fade_duration=0.1
)
```

### 4. Long Text Handling
For long Hindi texts, the engine automatically chunks at sentence boundaries:

```python
# Long text is automatically chunked
long_hindi_text = """
पहला पैराग्राफ। यहाँ बहुत सारा टेक्स्ट है।

दूसरा पैराग्राफ। और भी टेक्स्ट।

तीसरा पैराग्राफ। अंतिम टेक्स्ट।
"""

engine.generate(
    text=long_hindi_text,
    output_path="long_hindi.wav",
    voice="hf_beta"
)
# Automatically chunked and combined with smooth gaps
```

## Quality Considerations

Hindi voices have Grade C quality with MM minutes (10-100 minutes) of training data. For best results:

1. **Keep utterances in the 100-200 token range** for optimal quality
2. **Use proper Devanagari script** - avoid romanized Hindi
3. **Enable audio enhancement** for professional output
4. **Test different voices** - hf_alpha vs hf_beta may suit different tones
5. **Adjust speed** based on content type (0.9-1.2 range recommended)

## Troubleshooting

### Issue: "espeak-ng not found"
**Solution**: Install espeak-ng system-wide:
```bash
sudo apt-get install espeak-ng  # Linux
brew install espeak-ng          # macOS
```

### Issue: Hindi text sounds incorrect
**Solution**: 
- Verify text is in Devanagari script (not romanized)
- Check espeak-ng supports Hindi: `espeak-ng -v hi "नमस्ते" --stdout > test.wav`

### Issue: Audio quality is poor
**Solution**:
- Enable audio enhancement: `enhance=True`
- Use optimal token ranges (100-250 tokens)
- Adjust speed to 0.9-1.0 for clarity
- Try different Hindi voices (hf_alpha vs hf_beta)

### Issue: Rushed or cut-off speech
**Solution**:
- Text exceeds token limits - will be automatically chunked
- Check logs for chunking information
- Reduce chunk size if needed using config

## Example Project Structure

```
my_hindi_project/
├── scripts/
│   ├── hindi_intro.txt
│   ├── hindi_main.txt
│   └── hindi_outro.txt
├── outputs/
│   ├── hindi_intro.wav
│   ├── hindi_main.wav
│   └── hindi_outro.wav
├── generate_hindi.py
└── config.env
```

**generate_hindi.py**:
```python
from aparsoft_tts.core.engine import TTSEngine
from pathlib import Path

engine = TTSEngine()

scripts = Path("scripts").glob("*.txt")

for script in scripts:
    output_name = script.stem + ".wav"
    output_path = Path("outputs") / output_name
    
    with open(script, "r", encoding="utf-8") as f:
        text = f.read()
    
    print(f"Generating: {output_name}")
    engine.generate(
        text=text,
        output_path=output_path,
        voice="hf_alpha",
        speed=1.0
    )
    print(f"✓ Created: {output_path}")
```

## Additional Resources

- **Kokoro TTS Documentation**: https://huggingface.co/hexgrad/Kokoro-82M
- **Hindi Voices Details**: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- **espeak-ng Documentation**: https://github.com/espeak-ng/espeak-ng

## Support

For issues or questions:
1. Check logs for detailed error messages
2. Verify espeak-ng installation and Hindi support
3. Test with simple Hindi phrases first
4. Review this documentation for best practices

---

**Note**: Hindi support is production-ready and uses the same robust chunking and enhancement pipeline as English voices. All existing features (streaming, batch processing, podcasts) work seamlessly with Hindi voices.
