# Aparsoft TTS Streamlit - Quick Start Guide

Get the Streamlit management interface running in 2 minutes!

## Prerequisites

- Python 3.10 or higher
- 4GB+ RAM recommended
- Internet connection (for initial setup)

## Installation Steps

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update && sudo apt-get install -y espeak-ng ffmpeg libsndfile1
```

**macOS:**
```bash
brew install espeak ffmpeg
```

**Windows:**
- Download and install espeak-ng from http://espeak.sourceforge.net/
- Download and install FFmpeg from https://ffmpeg.org/download.html

### 2. Install Python Dependencies

```bash
# Navigate to project directory
cd /path/to/youtube-creator

# Install Streamlit and dependencies
pip install -r streamlit_requirements.txt

# Install aparsoft_tts package
pip install -e ".[mcp,cli]"
```

### 3. Run the App

**Choose one method:**

**Method A: Python Launcher (Recommended)**
```bash
python run_streamlit.py
```

**Method B: Bash Script (Linux/macOS)**
```bash
chmod +x run_streamlit.sh
./run_streamlit.sh
```

**Method C: Batch Script (Windows)**
```bash
run_streamlit.bat
```

**Method D: Direct Command**
```bash
streamlit run streamlit_app.py
```

### 4. Access the App

Open your browser and go to:
```
http://localhost:8501
```

## First-Time Usage

### 1. Generate Your First Audio

1. Click on "🎯 Single Generation" tab
2. Enter text: `"Welcome to Aparsoft TTS"`
3. Click "🎤 Generate Speech"
4. Listen to the audio and download it!

### 2. Try Different Voices

1. Go to "🔍 Voice Explorer" tab
2. Enter sample text
3. Click "Generate Sample" for different voices
4. Compare and choose your favorite

### 3. Process a Script

1. Navigate to "📄 Script Processing" tab
2. Paste a multi-paragraph script
3. Configure gap duration (0.5s recommended)
4. Click "🎬 Process Script"
5. Download your complete voiceover!

## Common Tasks

### Generate Audio with Custom Settings

```
1. Tab: Single Generation
2. Enter text
3. Select voice (e.g., am_michael)
4. Adjust speed (0.5x - 2.0x)
5. Toggle enhancement
6. Click Generate
```

### Batch Process Multiple Texts

```
1. Tab: Batch Processing
2. Choose "Manual Entry" or "File Upload"
3. Enter/upload your texts
4. Configure settings
5. Click "Generate Batch"
6. All files saved to outputs/batch/
```

### View Analytics

```
1. Tab: Analytics
2. See total generations
3. View charts and statistics
4. Export data as CSV/JSON
```

## Troubleshooting

### App Won't Start

**Error: "ModuleNotFoundError: No module named 'streamlit'"**

**Solution:**
```bash
pip install streamlit plotly pandas soundfile
```

**Error: "Port 8501 is already in use"**

**Solution:**
```bash
# Linux/macOS
lsof -ti:8501 | xargs kill -9

# Or use different port
streamlit run streamlit_app.py --server.port=8502
```

### Engine Not Initializing

**Error: "espeak-ng not found"**

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng

# macOS
brew install espeak
```

**Error: "Failed to load TTS model"**

**Solution:**
```bash
# Check if aparsoft_tts is installed
pip list | grep aparsoft-tts

# Reinstall if needed
pip install -e ".[mcp,cli]"
```

### Audio Not Playing

**Problem: No audio in browser**

**Solutions:**
1. Check browser audio permissions
2. Try downloading the file
3. Verify file was created in outputs/ directory
4. Test with external audio player

### Slow Generation

**Problem: Takes too long to generate**

**Solutions:**
1. Disable enhancement for quick drafts
2. Use faster speech speed (1.3x-1.5x)
3. Reduce text length
4. Check system resources (CPU/RAM)

## Tips & Tricks

### For YouTube Creators

```
Voice: am_michael
Speed: 1.0x
Enhancement: Enabled
Gap (scripts): 0.5s

This gives professional, clear voiceovers
perfect for tutorials and explainers.
```

### For Podcasts

```
Voice: af_bella or am_michael
Speed: 0.95x
Enhancement: Enabled
Gap: 0.3s

Slightly slower pace with warm tones
creates engaging podcast content.
```

### For Quick Drafts

```
Voice: Any
Speed: 1.3x - 1.5x
Enhancement: Disabled
Gap: 0.2s

Fast generation for testing scripts
before final production.
```

### For Professional Content

```
Voice: bm_george or bf_emma
Speed: 0.9x
Enhancement: Enabled
Gap: 0.5s

Slower, authoritative delivery
for formal presentations and docs.
```

## Keyboard Shortcuts

- `Ctrl/Cmd + R` - Reload app
- `Ctrl/Cmd + /` - Open command palette
- `s` - Toggle sidebar
- `k` - Open keyboard shortcuts help

## File Locations

```
outputs/
├── single/          # Single generations
├── batch/           # Batch outputs
│   └── YYYYMMDD_HHMMSS/
├── scripts/         # Script voiceovers
└── voice_samples/   # Voice comparisons

data/
└── generation_history.json

config/
└── custom_config.json

.streamlit/
└── config.toml
```

## Next Steps

1. **Explore All Features**
   - Try batch processing
   - Process a video script
   - Compare all voices
   - View analytics

2. **Customize Configuration**
   - Go to Configuration tab
   - Adjust default settings
   - Save custom configs

3. **Read Full Documentation**
   - `STREAMLIT_README.md` - Feature details
   - `README.md` - Core library docs

4. **Production Deployment**
   - Set up authentication
   - Configure SSL/HTTPS
   - Enable monitoring

## Getting Help

### Documentation
- `STREAMLIT_README.md` - App features
- `QUICKSTART.md` - TTS library guide
- `TUTORIAL.md` - Comprehensive tutorial

### Support
- 📧 Email: contact@aparsoft.com
- 🌐 Website: https://aparsoft.com
- 🐛 Issues: GitHub Issues

### Community
- Share your creations
- Report bugs
- Suggest features
- Contribute improvements

## Examples

### Example 1: YouTube Video Intro

```python
# Via Streamlit UI:
# Tab: Single Generation
# Text: "Welcome to my channel! In today's video, we'll explore amazing AI tools."
# Voice: am_michael
# Speed: 1.0x
# Enhancement: Enabled
```

### Example 2: Podcast Episode

```python
# Via Streamlit UI:
# Tab: Script Processing
# Upload: podcast_script.txt
# Voice: af_bella
# Speed: 0.95x
# Gap: 0.3s
```

### Example 3: Course Modules

```python
# Via Streamlit UI:
# Tab: Batch Processing
# Input: lesson_texts.txt (one per line)
# Voice: am_michael
# Speed: 1.0x
# Output: outputs/batch/TIMESTAMP/
```

## Performance Benchmarks

On typical hardware (i5/Ryzen 5, 8GB RAM):

- **Single Generation**: ~0.5-0.7s per second of audio
- **Batch (10 items)**: ~5-7s total
- **Script Processing**: ~1s per 100 words
- **Voice Comparison**: ~0.6s per voice

## Best Practices

1. **Test First**
   - Generate short samples
   - Try different voices
   - Find optimal settings

2. **Use Batch for Multiple Files**
   - More efficient than one-by-one
   - Consistent settings
   - Better organization

3. **Enable Enhancement for Final**
   - Disable for drafts
   - Enable for production
   - Results in professional quality

4. **Save Configurations**
   - Create presets for different use cases
   - Save time on repeated tasks
   - Maintain consistency

5. **Monitor History**
   - Track usage patterns
   - Identify popular voices
   - Optimize workflows

## Version Info

- **App Version**: 1.0.0
- **Streamlit**: 1.30.0+
- **Kokoro Model**: 82M parameters
- **Python**: 3.10+

## Updates

Check for updates regularly:

```bash
# Update dependencies
pip install --upgrade streamlit plotly pandas

# Update aparsoft_tts
cd /path/to/youtube-creator
git pull
pip install -e ".[mcp,cli]" --upgrade
```

---

**Happy Voice Generation! 🎙️**

*Start creating professional voiceovers in minutes!*
