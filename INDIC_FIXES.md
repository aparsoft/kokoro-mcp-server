# Issues Fixed - Indic Engine Setup

## Problems Found & Solutions

### ✅ Issue 1: pyproject.toml Configuration Error

**Problem:**
```
ValueError: Dependency #1 of option `indic` of field `project.optional-dependencies` 
cannot be a direct reference unless field `tool.hatch.metadata.allow-direct-references` 
is set to `true`
```

**Root Cause:**  
The `pyproject.toml` was using a direct GitHub URL for `parler-tts`:
```toml
indic = [
    "parler-tts @ git+https://github.com/huggingface/parler-tts.git",
    ...
]
```

Hatchling (the build backend) requires explicit permission to use direct Git URLs.

**Solution:**  
Added this configuration to `pyproject.toml`:
```toml
[tool.hatch.metadata]
allow-direct-references = true
```

**Status:** ✅ FIXED

---

### ✅ Issue 2: Test Script - FunctionTool Not Callable

**Problem:**
```
TypeError: 'FunctionTool' object is not callable
```

**Root Cause:**  
The test script was importing tools directly:
```python
from aparsoft_tts.mcp_server.mcp_tools import list_voices

await list_voices()  # ❌ This is a FunctionTool object, not a function!
```

When you use `@mcp.tool()` decorator, it wraps the function in a `FunctionTool` object for MCP registration. You can't call this wrapper directly.

**Solution:**  
Access the underlying async function via the `.fn` attribute:
```python
from aparsoft_tts.mcp_server.mcp_tools import (
    list_voices as list_voices_tool,
)

# Extract the actual callable function
list_voices = list_voices_tool.fn

# Now you can call it
await list_voices()  # ✅ Works!
```

**Status:** ✅ FIXED

---

### ℹ️ Note: Indic Engine Already Installed!

**Interesting Finding:**  
Despite the installation error, when you ran:
```bash
python -c "from aparsoft_tts.core.engine_indic_parler import IndicParlerEngine; print('✅ Indic engine installed')"
```

It showed: `✅ Indic engine installed`

**This means:**
- The Indic engine code is already present in the codebase
- The dependencies (parler-tts, transformers, etc.) are already installed
- The installation error was just about the `pyproject.toml` configuration, not actual functionality

---

## Next Steps

### 1. Verify the Fix

Try installing again (should work now):
```bash
cd /home/ram/projects/youtube-creator
pip install -e ".[indic]"
```

Expected: ✅ Should install without errors

### 2. Run the Tests

```bash
python test_mcp_indic.py
```

Expected: All tests should pass and generate audio files in `test_outputs/`

### 3. Test Indic Engine Manually

```bash
# Test Indic voices
python -c "
from aparsoft_tts.core.engine_factory import get_tts_engine
engine = get_tts_engine('indic')
print(engine.list_voices())
"
```

### 4. Generate Hindi Speech

Now you can use the Indic engine:
```python
from aparsoft_tts.mcp_server.mcp_server_main import GenerateSpeechRequest
from aparsoft_tts.mcp_server.mcp_tools import generate_speech

request = GenerateSpeechRequest(
    text="नमस्ते, मैं आपका स्वागत करता हूं। आज हम एक नई यात्रा शुरू करने जा रहे हैं।",
    voice="divya",
    engine="indic",
    emotion="neutral",
    output_file="test_outputs/hindi_sample.wav"
)

# Access the underlying function
result = await generate_speech.fn(request)
print(result)
```

---

## What Changed

### Files Modified:

1. **pyproject.toml**
   - Added: `[tool.hatch.metadata]` section
   - Added: `allow-direct-references = true`

2. **test_mcp_indic.py**
   - Changed: Import pattern to extract `.fn` from FunctionTool objects
   - Added: Proper function extraction before calling

---

## Why This Happened

### Direct GitHub References
Modern Python packaging tools (like pip and hatchling) have strict rules about package sources:
- ✅ Allowed: PyPI packages (`package>=1.0.0`)
- ⚠️ Needs Permission: Direct URLs (`package @ git+https://...`)

The `parler-tts` package isn't on PyPI yet, so it must be installed from GitHub. This requires the `allow-direct-references = true` flag.

### MCP Tool Decorators
FastMCP's `@mcp.tool()` decorator:
- Wraps functions in a `FunctionTool` class
- Used for tool registration and schema generation
- The actual function is stored in the `.fn` attribute

When testing, you need to access the real function, not the wrapper.

---

## Summary

✅ **pyproject.toml** - Fixed to allow direct GitHub references  
✅ **test_mcp_indic.py** - Fixed to call functions correctly  
✅ **Indic Engine** - Already installed and ready to use!  

You should now be able to:
- Install with `pip install -e ".[indic]"` without errors
- Run tests with `python test_mcp_indic.py` successfully
- Generate Hindi speech using the Indic engine with emotions!

**Try it now!** 🚀
