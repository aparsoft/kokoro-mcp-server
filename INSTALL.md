# Installation Guide - Multi-Engine Setup

## Overview

Aparsoft TTS now supports **three TTS engines** with modular installation:
- **Kokoro** (default): Fast, high-quality English TTS
- **Indic Parler-TTS** (optional): Professional Hindi + 21 Indic languages
- **OpenVoice** (optional): Voice cloning + multilingual

---

## Quick Install

### 1. **Minimal Install (Kokoro only)**
```bash
pip install -e .
```
**Includes:** Kokoro engine, core dependencies  
**Memory:** ~200MB  
**Best for:** English content only

### 2. **With Indic Engine (Hindi/Indic languages)**
```bash
pip install -e ".[indic]"
```
**Includes:** Kokoro + Indic Parler-TTS  
**Memory:** ~200MB (Kokoro) + ~1GB (Indic)  
**Best for:** English + Hindi/Indic content

### 3. **With All Engines**
```bash
pip install -e ".[engines]"
```
**Includes:** Kokoro + Indic + OpenVoice  
**Memory:** ~1.5GB total  
**Best for:** Multi-language + voice cloning

### 4. **Complete Install (Everything)**
```bash
pip install -e ".[complete]"
```
**Includes:** All engines + MCP server + CLI + STT + Streamlit  
**Memory:** ~2GB+ total  
**Best for:** Full feature set

### 5. **Development Install**
```bash
pip install -e ".[all]"
```
**Includes:** Everything + dev tools + docs  
**Best for:** Contributing to the project

---

## Installation Options Reference

| Option | Command | Includes |
|--------|---------|----------|
| **minimal** | `pip install -e .` | Kokoro only |
| **indic** | `pip install -e ".[indic]"` | + Indic Parler-TTS |
| **openvoice** | `pip install -e ".[openvoice]"` | + OpenVoice |
| **engines** | `pip install -e ".[engines]"` | All 3 engines |
| **mcp** | `pip install -e ".[mcp]"` | + MCP server |
| **stt** | `pip install -e ".[stt]"` | + Speech-to-text |
| **cli** | `pip install -e ".[cli]"` | + CLI interface |
| **streamlit** | `pip install -e ".[streamlit]"` | + Web interface |
| **complete** | `pip install -e ".[complete]"` | All features (no dev) |
| **all** | `pip install -e ".[all]"` | Everything + dev tools |

---

## Combining Options

You can combine multiple options:

```bash
# Indic engine + MCP server + CLI
pip install -e ".[indic,mcp,cli]"

# All engines + MCP server
pip install -e ".[engines,mcp]"

# Indic + STT + Streamlit
pip install -e ".[indic,stt,streamlit]"
```

---

## Verification

### Check Installation
```bash
python -c "from aparsoft_tts.core.engine_factory import get_tts_engine; print('✅ Kokoro installed')"
```

### Check Indic Engine
```bash
python -c "from aparsoft_tts.core.engine_indic_parler import IndicParlerEngine; print('✅ Indic engine installed')"
```

### Check All Engines
```bash
python -c "
from aparsoft_tts.core.engine_factory import get_engine_info
print(get_engine_info('kokoro'))
print(get_engine_info('indic'))
print(get_engine_info('openvoice'))
"
```

---

## Requirements by Engine

### Kokoro (Default)
```
kokoro>=0.9.2
soundfile>=0.12.1
librosa>=0.10.0
numpy>=1.24.0
scipy>=1.10.0
```

### Indic Parler-TTS
```
parler-tts (from GitHub)
transformers>=4.35.0
accelerate>=0.20.0
torch>=2.0.0
```

### OpenVoice
```
openvoice>=0.1.0
```

---

## Disk Space Requirements

| Component | First Install | After Model Download |
|-----------|---------------|----------------------|
| Kokoro | ~50MB | ~150MB |
| Indic Parler-TTS | ~100MB | ~2.6GB (auto-downloads) |
| OpenVoice | ~100MB | ~400MB |
| **Total (all engines)** | ~250MB | ~3.2GB |

**Note:** Models auto-download on first use (cached in `~/.cache/huggingface/`)

---

## Memory Usage (Runtime)

| Engine | Idle | Loaded | During Generation |
|--------|------|--------|-------------------|
| Kokoro | 0 | ~200MB | ~250MB |
| Indic | 0 | ~1GB | ~1.2GB |
| OpenVoice | 0 | ~300MB | ~350MB |

**With lazy loading:** Only requested engines consume memory!

---

## Platform-Specific Notes

### Linux
```bash
# May need system dependencies
sudo apt-get install libsndfile1 ffmpeg

# For Indic engine (optional, for better performance)
sudo apt-get install libopenblas-dev
```

### macOS
```bash
# Install via Homebrew
brew install libsndfile ffmpeg
```

### Windows
- Install Visual C++ Redistributable
- FFmpeg: Download from https://ffmpeg.org/download.html
- Add FFmpeg to PATH

---

## Troubleshooting

### "No module named 'parler_tts'"
```bash
pip install -e ".[indic]"
```

### "Torch not available"
```bash
# CPU-only (smaller)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# GPU (CUDA 11.8)
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### "Out of memory"
- Only install engines you need
- Use `pip install -e .` for Kokoro only (~200MB)
- Indic engine requires ~1GB RAM

### "Model download failed"
```bash
# Clear cache and retry
rm -rf ~/.cache/huggingface/hub/models--ai4bharat--indic-parler-tts
```

---

## Recommended Installations

### For English Content Only
```bash
pip install -e ".[mcp,cli]"
```
**~200MB, Kokoro engine**

### For Hindi/Indic Content
```bash
pip install -e ".[indic,mcp,cli]"
```
**~1.2GB, Kokoro + Indic**

### For Production API
```bash
pip install -e ".[engines,mcp]"
```
**~1.5GB, All engines + MCP server**

### For Development
```bash
pip install -e ".[all]"
```
**~2GB+, Everything**

---

## Upgrade

### Upgrade Core Package
```bash
pip install --upgrade -e .
```

### Upgrade with Dependencies
```bash
pip install --upgrade -e ".[complete]"
```

### Force Reinstall
```bash
pip install --force-reinstall -e ".[engines]"
```

---

## Uninstall

```bash
# Uninstall package
pip uninstall aparsoft-tts

# Clear model cache (optional, frees ~3GB)
rm -rf ~/.cache/huggingface/hub/models--ai4bharat--indic-parler-tts
rm -rf ~/.cache/huggingface/hub/models--kokoro-v0_19
```

---

## Next Steps

After installation:

1. **Test Kokoro:**
   ```bash
   python -c "from aparsoft_tts.core.engine_factory import get_tts_engine; e = get_tts_engine('kokoro'); print(e.list_voices())"
   ```

2. **Test Indic (if installed):**
   ```bash
   python test_indic_integration.py
   ```

3. **Start MCP Server (if installed):**
   ```bash
   python -m aparsoft_tts.mcp_server.run_server
   ```

4. **Start FastAPI (if installed):**
   ```bash
   cd aparsoft_tts/fastapi_aparsoft_tts
   python main.py
   ```

5. **Start Streamlit (if installed):**
   ```bash
   streamlit run streamlit_app.py
   ```

---

**Quick Start:** `pip install -e ".[indic,mcp,cli]"` for Hindi + MCP server! 🚀
