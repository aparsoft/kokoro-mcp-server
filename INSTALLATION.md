# Aparsoft TTS - Installation Guide

Quick reference for installing Aparsoft TTS with different feature sets.

## Installation Options

### 1. Core Package Only (Minimal)

Install just the TTS engine without MCP, CLI, or Streamlit:

```bash
pip install -e .
```

**Includes:**
- ✅ TTS Engine (Kokoro-82M)
- ✅ Audio processing
- ✅ Python API
- ❌ No MCP Server
- ❌ No CLI interface
- ❌ No Streamlit UI

**Use when:** You only need the Python API for your own projects.

---

### 2. With MCP + CLI (Recommended for Developers)

Install with MCP server and command-line interface:

```bash
pip install -e ".[mcp,cli]"
```

**Includes:**
- ✅ TTS Engine
- ✅ Audio processing
- ✅ Python API
- ✅ MCP Server (Claude Desktop, Cursor)
- ✅ CLI interface
- ❌ No Streamlit UI

**Use when:** You want MCP integration and CLI tools, but don't need the web UI.

---

### 3. With Streamlit UI

Install with Streamlit web interface:

```bash
pip install -e ".[streamlit]"
```

**Includes:**
- ✅ TTS Engine
- ✅ Audio processing
- ✅ Python API
- ✅ Streamlit web UI
- ❌ No MCP Server
- ❌ No CLI interface

**Use when:** You only want the web interface.

---

### 4. Complete Installation (Recommended for Most Users)

Install all user-facing features (MCP + CLI + Streamlit):

```bash
pip install -e ".[complete]"
```

**Or install individually:**
```bash
pip install -e ".[mcp,cli,streamlit]"
```

**Includes:**
- ✅ TTS Engine
- ✅ Audio processing
- ✅ Python API
- ✅ MCP Server (Claude Desktop, Cursor)
- ✅ CLI interface
- ✅ Streamlit web UI
- ❌ No development tools

**Use when:** You want all features for production use.

---

### 5. Full Installation with Development Tools

Install everything including development dependencies:

```bash
pip install -e ".[all]"
```

**Includes:**
- ✅ TTS Engine
- ✅ Audio processing
- ✅ Python API
- ✅ MCP Server
- ✅ CLI interface
- ✅ Streamlit web UI
- ✅ Development tools (pytest, black, ruff, mypy)
- ✅ Documentation tools (sphinx)

**Use when:** You're contributing to the project or need development tools.

---

## Quick Installation Commands

**Copy-paste ready commands:**

```bash
# OPTION 1: Core only
pip install -e .

# OPTION 2: MCP + CLI (most developers)
pip install -e ".[mcp,cli]"

# OPTION 3: Streamlit only
pip install -e ".[streamlit]"

# OPTION 4: Complete (recommended)
pip install -e ".[complete]"

# OPTION 5: Everything (contributors)
pip install -e ".[all]"
```

---

## Feature Comparison Table

| Feature | Core | mcp,cli | streamlit | complete | all |
|---------|------|---------|-----------|----------|-----|
| **TTS Engine** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Python API** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Audio Processing** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **MCP Server** | ❌ | ✅ | ❌ | ✅ | ✅ |
| **CLI Tools** | ❌ | ✅ | ❌ | ✅ | ✅ |
| **Streamlit UI** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Dev Tools** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Docs Tools** | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## After Installation

### Verify Installation

**Core:**
```bash
python -c "from aparsoft_tts import TTSEngine; print('✅ Core installed')"
```

**MCP:**
```bash
python -c "from fastmcp import FastMCP; print('✅ MCP installed')"
```

**CLI:**
```bash
aparsoft-tts --help
```

**Streamlit:**
```bash
python -c "import streamlit; print('✅ Streamlit installed')"
streamlit run streamlit_app.py
```

### System Dependencies

All installation options require these system packages:

**Ubuntu/Debian:**
```bash
sudo apt-get install espeak-ng ffmpeg libsndfile1
```

**macOS:**
```bash
brew install espeak ffmpeg
```

**Windows:**
- Download espeak-ng: http://espeak.sourceforge.net/
- Download FFmpeg: https://ffmpeg.org/download.html

---

## Troubleshooting

### ModuleNotFoundError

**Problem:** `ModuleNotFoundError: No module named 'streamlit'`

**Solution:**
```bash
# If you want Streamlit, install it:
pip install -e ".[streamlit]"

# Or install complete package:
pip install -e ".[complete]"
```

### Import Error

**Problem:** `ImportError: cannot import name 'TTSEngine'`

**Solution:**
```bash
# Reinstall the package
pip uninstall aparsoft-tts
pip install -e ".[complete]"
```

### Version Conflicts

**Problem:** Dependency version conflicts

**Solution:**
```bash
# Create fresh virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[complete]"
```

---

## Upgrading

**Upgrade to add more features:**

```bash
# You have core, want to add Streamlit:
pip install -e ".[streamlit]"

# You have mcp+cli, want to add Streamlit:
pip install -e ".[mcp,cli,streamlit]"

# Or just upgrade to complete:
pip install -e ".[complete]"
```

**Upgrade dependencies:**

```bash
# Upgrade all dependencies to latest versions
pip install --upgrade -e ".[complete]"
```

---

## Uninstallation

```bash
# Uninstall package
pip uninstall aparsoft-tts

# Remove generated files (optional)
rm -rf outputs/ data/ config/ temp/
```

---

## Summary

**Choose your installation based on your needs:**

- **Just the library?** → `pip install -e .`
- **Using with Claude/Cursor?** → `pip install -e ".[mcp,cli]"`
- **Want the web UI?** → `pip install -e ".[streamlit]"`
- **Want everything?** → `pip install -e ".[complete]"`
- **Contributing?** → `pip install -e ".[all]"`

**Most users should use:**
```bash
pip install -e ".[complete]"
```

This gives you all features (MCP + CLI + Streamlit) without dev dependencies.
