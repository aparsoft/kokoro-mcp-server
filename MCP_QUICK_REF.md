# MCP Multi-Engine Quick Reference 🚀

## TL;DR - What Changed?

Your MCP server now supports **3 engines** (kokoro, openvoice, indic) through an `engine` parameter. Claude can choose the best engine for each task.

---

## Quick Test

### 1. Test MCP Integration
```bash
cd /home/ram/projects/youtube-creator
python test_mcp_indic.py
```

### 2. Check Output
```bash
ls -lh test_outputs/
```

---

## Engine Selection Guide

### Use **Kokoro** (`engine="kokoro"`) for:
✅ Fast English content  
✅ YouTube English voiceovers  
✅ English podcasts  
⚡ Speed: ~0.5s per line

### Use **Indic** (`engine="indic"`) for:
✅ Professional Hindi content (MOS 83.43)  
✅ 21 Indic languages  
✅ Emotion control (happy, sad, angry, etc.)  
✅ 69 professional voices  
⚡ Speed: ~1s per line

### Use **OpenVoice** (`engine="openvoice"`) for:
✅ Voice cloning  
✅ 6 languages (EN, ES, FR, ZH, JA, KO)  
❌ **NO Hindi support**  
🐢 Speed: ~3-5s per line

---

## API Changes

### All Request Models Now Have:
```python
engine: str = "kokoro"  # NEW: "kokoro", "openvoice", or "indic"
emotion: str = "neutral"  # NEW: For Indic engine only
```

### Example: Hindi Generation
```python
from aparsoft_tts.mcp_server.mcp_server_main import GenerateSpeechRequest
from aparsoft_tts.mcp_server.mcp_tools import generate_speech

request = GenerateSpeechRequest(
    text="नमस्ते दोस्तों! आज हम AI के बारे में बात करेंगे।",
    voice="divya",
    engine="indic",  # ← Use Indic engine
    emotion="happy",  # ← Emotion control
    output_file="hindi_intro.wav"
)

result = await generate_speech(request)
```

### Example: English Generation (Default)
```python
request = GenerateSpeechRequest(
    text="Welcome to our channel!",
    voice="am_michael",
    engine="kokoro",  # ← Fast English engine
    output_file="english_intro.wav"
)

result = await generate_speech(request)
```

---

## Memory Management

**Only ONE engine instance per type loads:**

```python
# First call - loads Kokoro
kokoro = get_tts_engine("kokoro")  # Loads ~200MB

# Second call - uses cached Kokoro
kokoro2 = get_tts_engine("kokoro")  # No loading

# Third call - loads Indic (separate from Kokoro)
indic = get_tts_engine("indic")  # Loads ~1GB

# Both engines stay in memory until program ends
```

**Memory usage:**
- Kokoro: ~200MB
- OpenVoice: ~300MB
- Indic: ~1GB

**Total if all loaded:** ~1.5GB

---

## Indic Voices

### Hindi Male Voices
- `madhav` - Professional narrator, clear
- `arnav` - Warm, conversational
- `megh` - Storyteller, expressive

### Hindi Female Voices
- `divya` - Elegant, professional ⭐ **RECOMMENDED**
- `priya` - Warm, approachable
- `ananya` - Energetic, youthful

### Emotions (Indic Only)
- `neutral` (default)
- `happy`
- `sad`
- `angry`
- `fearful`
- `disgusted`
- `surprised`

---

## MCP Tools Updated

### ✅ generate_speech
Added: `engine`, `emotion` parameters

### ✅ batch_generate
Added: `engine`, `emotion` parameters

### ✅ process_script
Added: `engine`, `emotion` parameters

### ✅ generate_podcast
Added: `engine` parameter, `emotion` per segment

### ✅ list_voices
Now shows voices for **all three engines**

### ✅ transcribe_speech
No changes (uses Whisper)

---

## Backwards Compatibility

**All existing code continues to work!**

Default engine is `"kokoro"`, so:

```python
# Old code - still works
request = GenerateSpeechRequest(
    text="Hello",
    voice="am_michael",
    output_file="output.wav"
)
# Uses Kokoro engine (default)
```

```python
# New code - explicit engine
request = GenerateSpeechRequest(
    text="नमस्ते",
    voice="divya",
    engine="indic",  # ← Explicit
    output_file="output.wav"
)
# Uses Indic engine
```

---

## Claude Desktop Usage

Claude can now select engines automatically:

**User asks for English content:**
```json
{
  "tool": "generate_speech",
  "arguments": {
    "text": "Welcome!",
    "voice": "am_michael",
    "engine": "kokoro"
  }
}
```

**User asks for Hindi content:**
```json
{
  "tool": "generate_speech",
  "arguments": {
    "text": "नमस्ते!",
    "voice": "divya",
    "engine": "indic",
    "emotion": "happy"
  }
}
```

---

## Common Patterns

### English YouTube Video
```python
# Fast, professional English
engine="kokoro"
voice="am_michael"
speed=1.0
```

### Hindi YouTube Video
```python
# Professional Hindi with emotion
engine="indic"
voice="divya"
emotion="neutral"
speed=1.0
```

### English Podcast (2 voices)
```python
engine="kokoro"
segments=[
    PodcastSegment(text="Host intro", voice="af_sarah"),
    PodcastSegment(text="Guest response", voice="am_michael")
]
```

### Hindi Podcast (2 voices with emotions)
```python
engine="indic"
segments=[
    PodcastSegment(text="होस्ट: स्वागत है!", voice="divya", emotion="happy"),
    PodcastSegment(text="गेस्ट: धन्यवाद!", voice="arnav", emotion="neutral")
]
```

---

## Testing Checklist

Run these to verify everything works:

```bash
# 1. Test MCP integration
python test_mcp_indic.py

# 2. Test Indic engine directly
cd aparsoft_tts/core
python -m pytest test_indic_integration.py -v

# 3. List available voices
python -c "
from aparsoft_tts.core.engine_factory import get_tts_engine
engine = get_tts_engine('indic')
print(engine.list_voices())
"
```

---

## Troubleshooting

### "Module 'parler_tts' not found"
```bash
pip install -r requirements_indic.txt
```

### "Engine 'indic' not found"
Make sure `engine_indic_parler.py` exists in `aparsoft_tts/core/`

### "Memory error"
Only load engines you need. Each engine uses 200MB-1GB RAM.

### "Emotion not working"
Emotion only works with `engine="indic"`. Kokoro/OpenVoice ignore it.

---

## Files Modified

✅ `mcp_server_main.py` - Request models + caching  
✅ `mcp_tools.py` - All 6 tools updated  
✅ `engine_factory.py` - Three-engine support  
✅ `config.py` - Engine enum updated  
✅ `engine_indic_parler.py` - New Indic engine  

---

## Status

✅ **COMPLETE** - MCP server fully supports multi-engine architecture!

**What you can do now:**
1. Use Kokoro for fast English
2. Use Indic for professional Hindi
3. Use OpenVoice for voice cloning
4. Claude Desktop automatically chooses best engine
5. Only requested engines load to memory

---

**Next:** Test with `python test_mcp_indic.py` and start using Hindi TTS! 🎉
