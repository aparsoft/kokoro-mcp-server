# 🎙️ Aparsoft TTS - Quick Reference Card

## Installation Cheat Sheet

```bash
# Complete (RECOMMENDED) - All features
pip install -e ".[complete]"

# Developers - No Streamlit
pip install -e ".[mcp,cli]"

# Streamlit Only
pip install -e ".[streamlit]"

# Core Only
pip install -e .

# Everything + Dev Tools
pip install -e ".[all]"
```

## Launch Commands

```bash
# Streamlit Web UI
python run_streamlit.py          # Cross-platform
./run_streamlit.sh               # Linux/macOS
run_streamlit.bat                # Windows
streamlit run streamlit_app.py   # Direct

# CLI
aparsoft-tts generate "text" -o file.wav
aparsoft-tts voices
aparsoft-tts script file.txt -o output.wav

# MCP Server
python -m aparsoft_tts.mcp_server              # Run server (auto in Claude/Cursor)
python -m aparsoft_tts.mcp_server --help       # Test if server works
npx @modelcontextprotocol/inspector \          # Interactive testing UI
  --command "/path/to/venv/bin/python" \
  --args "-m" "aparsoft_tts.mcp_server"
```

## Common Tasks

### Generate Single Audio
**Streamlit:** Single Generation tab → Enter text → Generate
**CLI:** `aparsoft-tts generate "text" -o output.wav`
**Python:**
```python
from aparsoft_tts import TTSEngine
engine = TTSEngine()
engine.generate("text", "output.wav")
```

### Batch Processing
**Streamlit:** Batch Processing tab → Upload/Enter texts → Generate
**CLI:** `aparsoft-tts batch "Text 1" "Text 2" -d outputs/`
**Python:**
```python
engine.batch_generate(["Text 1", "Text 2"], "outputs/")
```

### Process Script
**Streamlit:** Script Processing tab → Upload/Paste → Process
**CLI:** `aparsoft-tts script file.txt -o voiceover.wav`
**Python:**
```python
engine.process_script("file.txt", "voiceover.wav")
```

### Compare Voices
**Streamlit:** Voice Explorer tab → Generate samples
**CLI:** Generate samples with different -v flags
```bash
aparsoft-tts generate "Test" -v am_michael -o m1.wav
aparsoft-tts generate "Test" -v bm_george -o m2.wav
```

## Available Voices

**Male:** am_adam, am_michael⭐, bm_george, bm_lewis
**Female:** af_bella, af_nicole, af_sarah, af_sky, bf_emma, bf_isabella

## Key Parameters

| Parameter | Range | Default | Use Case |
|-----------|-------|---------|----------|
| speed | 0.5-2.0 | 1.0 | 0.9=slow, 1.0=normal, 1.3=fast |
| enhance | true/false | true | Production=true, Draft=false |
| voice | See above | am_michael | Professional=am_michael |
| gap | 0.0-5.0s | 0.5s | Pause between segments |

## Quick Troubleshooting

```bash
# App won't start
pip install streamlit plotly pandas

# Engine not initializing
sudo apt-get install espeak-ng ffmpeg  # Ubuntu
brew install espeak ffmpeg             # macOS

# Port in use
streamlit run streamlit_app.py --server.port=8502

# Module not found
pip install -e ".[complete]"
```

## File Locations

```
outputs/single/         # Single generations
outputs/batch/          # Batch processing
outputs/scripts/        # Script voiceovers
outputs/voice_samples/  # Voice comparisons
data/generation_history.json  # History
config/custom_config.json     # Saved configs
```

## Documentation

- `INSTALLATION.md` - Installation guide
- `STREAMLIT_QUICKSTART.md` - Quick start
- `STREAMLIT_README.md` - Full features
- `README.md` - Core library

## Streamlit Tabs

1. 🎯 **Single Generation** - One text → one audio
2. 📦 **Batch Processing** - Multiple texts → multiple audios
3. 📄 **Script Processing** - Full script → complete voiceover
4. 🔍 **Voice Explorer** - Compare all voices
5. ⚙️ **Configuration** - Manage settings
6. 📊 **Analytics** - View statistics & history

## Best Practices

### YouTube Tutorial
```
Voice: am_michael
Speed: 1.0x
Enhancement: Enabled
Gap: 0.5s
```

### Podcast
```
Voice: af_bella
Speed: 0.95x
Enhancement: Enabled
Gap: 0.3s
```

### Quick Draft
```
Voice: Any
Speed: 1.3x
Enhancement: Disabled
```

### Professional
```
Voice: bm_george
Speed: 0.9x
Enhancement: Enabled
Gap: 0.5s
```

## URLs

- **Streamlit:** http://localhost:8501
- **MCP Inspector:** http://localhost:6274
- **Website:** https://aparsoft.com

## MCP Server Testing

**Test Server Runs:**
```bash
python -m aparsoft_tts.mcp_server --help
```

**Test with Claude/Cursor:**
```
# In Claude Desktop or Cursor, ask:
"Generate speech for 'Welcome to our channel' using am_michael voice and save as intro.wav"

"List all available TTS voices"

"Process script.txt and create voiceover with 0.8s gaps"
```

**Interactive Testing (MCP Inspector):**
```bash
npx @modelcontextprotocol/inspector \
  --command "/path/to/venv/bin/python" \
  --args "-m" "aparsoft_tts.mcp_server"
# Opens UI at http://localhost:6274
```

## Support

- 📧 contact@aparsoft.com
- 🌐 aparsoft.com
- 📖 See documentation files

## Version Info

- **App Version:** 1.0.0
- **Python:** 3.10+
- **Streamlit:** 1.30+
- **Kokoro:** 82M params

---

**💡 Pro Tip:** Install with `pip install -e ".[complete]"` to get all features!

**Last Updated:** 2025-10-05
