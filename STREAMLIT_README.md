# Aparsoft TTS - Streamlit Management Interface

An enterprise-grade web interface for managing Aparsoft TTS functionality with **multi-engine support**.

## 🚀 Multi-Engine Support

Choose from three powerful TTS engines:

### 🚀 Kokoro (Fast English)
- **Model**: 82M parameters
- **Languages**: English (primary), Hindi (Grade C - 4 voices)
- **Speed**: ⚡ Very Fast (~0.5s per second of audio)
- **Best for**: Quick English content, tutorials, drafts

### �🇳 Indic Parler-TTS (Professional Hindi)
- **Model**: 900M parameters (AI4Bharat)
- **Languages**: 21 Indic languages (Hindi, Bengali, Tamil, Telugu, etc.)
- **Quality**: 🏆 83.43 MOS for Hindi (professional grade)
- **Voices**: 69 unique voices across languages
- **Emotions**: 10 emotions (neutral, happy, sad, angry, narration, etc.)
- **Best for**: Hindi podcasts, educational content, professional voiceovers

### 🎭 OpenVoice V2 (Voice Cloning)
- **Model**: Multi-lingual voice cloning
- **Languages**: English, Spanish, French, Chinese, Japanese, Korean
- **Feature**: Clone any voice from 3-second reference audio
- **Best for**: Custom voice matching, character voices, brand consistency

## Features

### �🎯 Single Generation
- Convert text to speech with real-time preview
- **Engine selection** - Choose Kokoro, Indic, or OpenVoice
- **Emotion control** - 10 emotions for Indic engine
- Customizable voice, speed, and enhancement settings
- Instant audio playback and download
- Detailed generation metrics

### 📦 Batch Processing
- Process multiple texts in one go
- Manual entry or file upload
- Progress tracking
- Batch download capability

### 📄 Script Processing
- Convert complete video scripts to voiceovers
- Automatic text chunking for optimal quality
- Configurable gap between segments
- Perfect for YouTube, podcasts, and presentations

### 🔍 Voice Explorer
- Compare all 12 available voices
- Side-by-side voice comparison
- Sample generation for each voice
- Detailed voice characteristics

### ⚙️ Configuration
- Manage TTS engine settings
- Audio processing parameters
- Save and load custom configurations
- Real-time configuration preview

### 📊 Analytics
- Generation history tracking
- Visual analytics and charts
- Voice usage statistics
- Timeline visualization
- Export data (CSV/JSON)

## Quick Start

### Installation

```bash
# Navigate to project directory
cd /path/to/youtube-creator

# Install base dependencies
pip install streamlit plotly pandas

# Install with specific engines (choose one):

# Option 1: Kokoro only (fastest, smallest)
pip install -e .

# Option 2: With Indic engine (professional Hindi)
pip install -e ".[indic]"

# Option 3: With OpenVoice (voice cloning)
pip install -e ".[openvoice]"

# Option 4: All engines (complete installation)
pip install -e ".[complete]"

# Run the app
streamlit run streamlit_app.py
```

### Alternative: Use the startup script

```bash
# Make script executable
chmod +x run_streamlit.sh

# Run the app
./run_streamlit.sh
```

## Usage Guide

### 1. Single Speech Generation

1. **Select Engine** in sidebar (Kokoro/Indic/OpenVoice)
2. Navigate to the "Single Generation" tab
3. Enter your text (up to 10,000 characters)
4. Select voice from available voices for chosen engine
5. **(Indic only)** Select emotion (neutral, happy, sad, etc.)
6. Configure speed and enhancement options
7. Click "Generate Speech"
8. Preview audio and download

**Engine-specific tips:**
- **Kokoro**: Best for English, use `am_michael` for professional sound
- **Indic**: Best for Hindi, use `rohit` (male) or `divya` (female), select emotion
- **OpenVoice**: Upload reference audio for voice cloning

### 2. Batch Processing

**Method 1: Manual Entry**
1. Select "Manual Entry" input method
2. Specify number of texts
3. Enter each text
4. Configure settings
5. Click "Generate Batch"

**Method 2: File Upload**
1. Select "File Upload" input method
2. Upload a text file (one text per line)
3. Preview loaded texts
4. Configure settings
5. Click "Generate Batch"

### 3. Script Processing

**Method 1: Direct Text**
1. Select "Direct Text" input method
2. Paste your script
3. Configure voice, speed, and gap settings
4. Click "Process Script"

**Method 2: File Upload**
1. Select "Upload File" input method
2. Upload .txt or .md script file
3. Preview script
4. Configure settings
5. Click "Process Script"

### 4. Voice Comparison

1. Navigate to "Voice Explorer" tab
2. Enter comparison text
3. Generate samples for different voices
4. Listen and compare
5. Choose your favorite voice

### 5. Configuration Management

1. Go to "Configuration" tab
2. Adjust TTS and audio processing settings
3. Click "Save Configuration"
4. Engine will reload with new settings

### 6. Analytics Dashboard

1. Navigate to "Analytics" tab
2. View summary metrics
3. Explore charts and visualizations
4. Check generation history
5. Export data as needed

## Features in Detail

### Audio Enhancement

The app includes professional audio processing:

- **Normalization**: Consistent volume levels
- **Silence Trimming**: Remove dead air
- **Noise Reduction**: Spectral gating
- **Fade In/Out**: Smooth transitions

### Voice Options

**Kokoro Engine - English Voices:**

**Male Voices:**
- `am_adam` - American, natural inflection
- `am_michael` - American, professional (⭐ recommended)
- `bm_george` - British, authoritative
- `bm_lewis` - British, modern

**Female Voices:**
- `af_bella` - American, warm
- `af_nicole` - American, dynamic
- `af_sarah` - American, clear
- `af_sky` - American, youthful
- `bf_emma` - British, professional
- `bf_isabella` - British, gentle

**Indic Engine - Hindi Voices (Recommended):**
- `rohit` - Male, clear and professional
- `divya` - Female, warm and engaging
- `aman` - Male, energetic
- `rani` - Female, authoritative

**Plus 65+ voices for 20 other Indic languages!**

**Indic Emotions:**
- `neutral` - Standard delivery
- `happy` - Upbeat and cheerful
- `sad` - Melancholic tone
- `angry` - Strong and intense
- `narration` - Storytelling style
- `conversation` - Natural dialogue
- `command` - Authoritative
- `disgust` - Negative emotion
- `fear` - Anxious tone
- `surprise` - Excited and amazed

**OpenVoice Engine:**
- Uses reference audio for voice cloning
- Can match any voice from 3+ seconds of audio
- Supports multiple languages

### Generation Metrics

For each generation, the app tracks:
- Audio duration
- File size
- Generation time
- Voice used
- Speed setting
- Enhancement status

### History & Analytics

The app maintains a complete history of all generations with:
- Type distribution (single/batch/script)
- Voice usage statistics
- Daily generation timeline
- Recent activity table
- Export capabilities (CSV/JSON)

## Output Directories

```
outputs/
├── single/          # Single generations
├── batch/           # Batch processing outputs
│   └── YYYYMMDD_HHMMSS/  # Timestamped batch folders
├── scripts/         # Script processing outputs
└── voice_samples/   # Voice comparison samples

data/
└── generation_history.json  # Generation history

config/
└── custom_config.json  # Saved configurations

temp/
└── scripts/         # Temporary script files
```

## Keyboard Shortcuts

- `Ctrl + R` / `Cmd + R` - Reload app
- `Ctrl + /` / `Cmd + /` - Open command palette
- `s` - Open sidebar settings

## Troubleshooting

### App won't start

```bash
# Check if Streamlit is installed
pip list | grep streamlit

# Reinstall if needed
pip install streamlit

# Try running with --server.headless=false
streamlit run streamlit_app.py --server.headless=false
```

### Engine initialization fails

1. Check if espeak-ng is installed
2. Verify Python version (3.10+)
3. Ensure aparsoft_tts package is installed
4. Check logs in sidebar

### Audio not playing

1. Check browser audio permissions
2. Try downloading and playing externally
3. Verify output file exists
4. Check file format compatibility

### Slow generation

1. Disable audio enhancement for drafts
2. Use faster voice (am_michael)
3. Reduce text length
4. Check system resources

## Advanced Features

### Engine Selection & Lazy Loading

The app uses **lazy loading** - engines are loaded only when first used:

1. Select engine in sidebar
2. Engine loads on first generation
3. Only one engine in memory at a time
4. Switch engines anytime (previous engine unloads)

**Memory efficiency:**
- Kokoro: ~200MB
- Indic: ~2GB (loaded only when selected)
- OpenVoice: ~1GB (loaded only when selected)

### Custom Configuration

Save custom configurations for different use cases:

```python
# YouTube Tutorial Config (Kokoro)
{
  "engine": "kokoro",
  "voice": "am_michael",
  "speed": 1.0,
  "enhance_audio": true,
  "sample_rate": 24000
}

# Hindi Podcast Config (Indic)
{
  "engine": "indic",
  "voice": "divya",
  "emotion": "narration",
  "speed": 0.95,
  "enhance_audio": true,
  "sample_rate": 44100
}

# Custom Voice Config (OpenVoice)
{
  "engine": "openvoice",
  "reference_audio": "path/to/reference.wav",
  "speed": 1.0,
  "enhance_audio": true
}
```

### Batch Upload Format

Create a text file with one text per line:

```
Welcome to our channel
In this video we'll discuss AI
Subscribe for more content
```

### Script Format

For best results, format scripts with clear paragraphs:

```
Introduction paragraph here.

Main content paragraph here with important details.

Conclusion and call to action here.
```

## Performance Tips

### Engine-Specific Tips

**Kokoro (English):**
1. **For Quick Drafts**: Speed 1.3x, no enhancement
2. **For Production**: Speed 1.0x, enable enhancement
3. **Best Voice**: `am_michael` for professional content

**Indic (Hindi):**
1. **For Podcasts**: Use `divya` voice, `narration` emotion, speed 0.95x
2. **For Education**: Use `rohit` voice, `neutral` emotion, speed 0.9x
3. **For Entertainment**: Use `happy` or `surprise` emotions
4. **Quality**: Always enable enhancement for production

**OpenVoice (Cloning):**
1. **Reference Audio**: Use 3-10 seconds, clear recording
2. **Best Results**: Studio-quality reference gives best clones
3. **Speed**: Adjust based on reference voice characteristics

### General Performance

1. **For Quick Drafts**: Disable enhancement, use speed 1.3x
2. **For Production**: Enable enhancement, use speed 1.0x
3. **For Learning Content**: Use speed 0.9x, enable enhancement
4. **For Batch Jobs**: Process during off-hours, use batch processing

### Memory Management

- Only one engine loads at a time (lazy loading)
- Switching engines clears previous engine from memory
- Kokoro: Fastest loading (~2s)
- Indic: Slower loading (~10-15s first time)
- OpenVoice: Medium loading (~5-7s)

## Security

The app:
- Runs locally (no data sent to external servers)
- Stores files only in specified output directories
- Uses local TTS engine (no API calls)
- Maintains privacy of all content

## Support

### Getting Help

- 📧 Email: contact@aparsoft.com
- 🌐 Website: https://aparsoft.com
- 📖 Docs: See main README.md

### Reporting Issues

When reporting issues, include:
1. Error message (if any)
2. Steps to reproduce
3. Input text used
4. Configuration settings
5. Browser and OS version

## Roadmap

Planned features:
- [ ] Real-time streaming preview
- [ ] Multi-language support
- [ ] Custom voice training
- [ ] API endpoint integration
- [ ] Cloud storage integration
- [ ] Team collaboration features
- [ ] Scheduled generation
- [ ] Webhook notifications

## Credits

Built with:
- **Streamlit** - Web interface
- **Plotly** - Interactive charts
- **Pandas** - Data processing
- **Kokoro-82M** - TTS engine
- **aparsoft_tts** - Core TTS library

## License

Same as parent project (Apache 2.0)

---

**Happy Voice Generation! 🎙️**
