# 🎙️ Aparsoft YouTube TTS System

**Production-Ready Text-to-Speech Solution for YouTube Videos**

A comprehensive, open-source text-to-speech system using state-of-the-art Hugging Face models, audio enhancement with librosa, and Model Context Protocol (MCP) server integration. Built specifically for creating professional voiceovers without relying on paid services like ElevenLabs.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-Models-yellow)](https://huggingface.co/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Why This Solution?](#why-this-solution)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [MCP Server Setup](#mcp-server-setup)
- [Advanced Features](#advanced-features)
- [API Reference](#api-reference)
- [Model Comparison](#model-comparison)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

This TTS system is designed for **Aparsoft's YouTube content creation**, providing:

- **High-Quality Voice Generation**: Using Kokoro-82M (82M parameters, #1 trending on Hugging Face)
- **Audio Enhancement**: Professional-grade audio processing with librosa
- **MCP Integration**: Automated workflows via Model Context Protocol servers
- **100% Open Source**: No API costs, complete control

### Why We Built This

Creating YouTube videos requires consistent, professional voiceovers. Instead of:
- ❌ Paying for ElevenLabs ($22-99/month)
- ❌ Using non-native English (limiting reach)
- ❌ Inconsistent voice quality

We built a system that:
- ✅ Generates high-quality male voices for free
- ✅ Enhances audio for broadcast quality
- ✅ Automates voiceover creation
- ✅ Integrates with our development workflow

---

## ✨ Key Features

### 🎤 **Multiple TTS Models**
- **Kokoro-82M** (Recommended): 82M parameters, 44% win rate on TTS Arena
- **Parler-TTS**: Controllable voice with text descriptions (880M/2.3B)
- **Chatterbox**: Fast, efficient, natural speech (500M)

### 🔊 **Audio Enhancement**
- Noise reduction using spectral gating
- Automatic normalization and trimming
- Fade in/out for smooth transitions
- Professional broadcast-quality output

### 🔌 **MCP Server Integration**
- Standardized text-to-speech API
- Compatible with Claude Desktop, Cursor, Cline
- Automated workflow integration
- Real-time voice generation

### 🎬 **YouTube-Optimized**
- Segment-based script processing
- Automatic audio combining
- Gap management between segments
- Export-ready audio files

---

## 🤔 Why This Solution?

### Traditional Approach vs. Our Solution

| Aspect | Traditional (ElevenLabs) | Our Solution |
|--------|-------------------------|--------------|
| **Cost** | $22-99/month | Free (open-source) |
| **Quality** | Excellent | Comparable (Kokoro) |
| **Control** | Limited | Complete |
| **Privacy** | Cloud-based | Local |
| **Customization** | API limits | Unlimited |
| **Latency** | API dependent | Local (faster) |

### Technical Advantages

1. **No Vendor Lock-in**: Own your voice generation pipeline
2. **Scalability**: Run on your infrastructure, scale as needed
3. **Customization**: Mix voices, adjust parameters, enhance audio
4. **Integration**: MCP protocol for seamless AI workflows

---

## 🚀 Quick Start

### 5-Minute Setup

```bash
# 1. Create virtual environment
python -m venv tts_env
source tts_env/bin/activate  # Windows: tts_env\Scripts\activate

# 2. Install dependencies
pip install kokoro>=0.9.2 soundfile librosa numpy scipy

# 3. Install espeak (required)
# Ubuntu/Debian:
sudo apt-get install espeak-ng
# macOS:
brew install espeak
# Windows: Download from http://espeak.sourceforge.net/

# 4. Test it!
python quick_test.py
```

### Quick Test Script

```python
# quick_test.py
from kokoro import KPipeline
import soundfile as sf
import numpy as np

# Initialize
pipeline = KPipeline(lang_code='a')  # 'a' = American English

# Generate speech
text = "Welcome to Aparsoft. We deploy AI solutions in 10 days."
generator = pipeline(text, voice='am_michael', speed=1.0)

# Combine audio chunks
audio = np.concatenate([chunk for _, _, chunk in generator])

# Save
sf.write('test_output.wav', audio, 24000)
print("✅ Success! Check test_output.wav")
```

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- 4GB RAM minimum
- 1GB disk space for models
- `espeak-ng` system package

### Step-by-Step Installation

#### 1. **Clone or Download**

```bash
# If using git
git clone https://github.com/aparsoft/youtube-tts.git
cd youtube-tts

# Or download and extract ZIP
```

#### 2. **Install Python Dependencies**

```bash
# Create virtual environment
python -m venv tts_env
source tts_env/bin/activate  # Windows: tts_env\Scripts\activate

# Install core packages
pip install kokoro>=0.9.2
pip install soundfile librosa numpy scipy

# For MCP server (optional)
pip install fastmcp mcp

# For advanced features (optional)
pip install torch transformers
```

#### 3. **Install System Dependencies**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install espeak-ng ffmpeg
```

**macOS:**
```bash
brew install espeak ffmpeg
```

**Windows:**
- Download espeak from: http://espeak.sourceforge.net/
- Download ffmpeg from: https://ffmpeg.org/download.html
- Add to PATH

#### 4. **Verify Installation**

```bash
python -c "from kokoro import KPipeline; print('✅ Kokoro installed')"
python -c "import librosa; print('✅ Librosa installed')"
python -c "import soundfile; print('✅ Soundfile installed')"
```

---

## 💻 Usage

### Basic Usage

#### **Option 1: Simple Script**

```python
from kokoro import KPipeline
import soundfile as sf
import numpy as np

# Initialize pipeline
pipeline = KPipeline(lang_code='a')

# Your text
text = """
Hi, I'm from Aparsoft. In this tutorial, 
we'll show you how to deploy AI chatbots in just 10 days.
"""

# Generate speech
generator = pipeline(text, voice='am_michael', speed=1.0)
audio = np.concatenate([chunk for _, _, chunk in generator])

# Save to file
sf.write('output.wav', audio, 24000)
```

#### **Option 2: Using Our YouTube TTS Class**

```python
from youtube_tts import YouTubeTTS

# Initialize with male voice
tts = YouTubeTTS(voice='am_michael', lang_code='a')

# Generate with enhancement
tts.text_to_speech(
    text="Your script here",
    output_file="voiceover.wav",
    speed=1.0,
    enhance_audio=True  # Applies librosa enhancement
)
```

#### **Option 3: Batch Processing**

```python
from youtube_tts import YouTubeTTS

tts = YouTubeTTS(voice='am_michael')

scripts = [
    "Welcome to our channel",
    "In this video, we'll cover AI deployment",
    "Don't forget to subscribe!"
]

tts.batch_generate(scripts, output_dir='outputs')
# Creates: outputs/audio_1.wav, outputs/audio_2.wav, etc.
```

### Available Voices

**Male Voices (Recommended for Aparsoft):**
- `am_michael` - Professional American male ⭐ **Recommended**
- `bm_george` - British male, formal
- `am_adam` - American male, younger tone

**Female Voices:**
- `af_bella` - American female, warm
- `af_heart` - American female, expressive
- `bf_emma` - British female, professional

**Test all voices:**
```python
voices = ['am_michael', 'bm_george', 'am_adam']
for voice in voices:
    tts = YouTubeTTS(voice=voice)
    tts.text_to_speech(f"Testing {voice} voice", f"{voice}_test.wav")
```

---

## 🔧 Complete Implementation

### Main TTS Module (`youtube_tts.py`)

```python
import soundfile as sf
from kokoro import KPipeline
import librosa
import numpy as np
import os

class YouTubeTTS:
    """Production-ready TTS for YouTube videos"""
    
    def __init__(self, voice='am_michael', lang_code='a'):
        """
        Initialize TTS system
        
        Args:
            voice: Voice ID (am_michael, bm_george, am_adam, etc.)
            lang_code: 'a' for American, 'b' for British English
        """
        self.pipeline = KPipeline(lang_code=lang_code)
        self.voice = voice
        self.sample_rate = 24000
        
    def text_to_speech(self, text, output_file='output.wav', 
                       speed=1.0, enhance_audio=True):
        """
        Convert text to speech
        
        Args:
            text: Input text
            output_file: Output filename
            speed: Speech speed (0.5-2.0)
            enhance_audio: Apply audio enhancement
        
        Returns:
            Path to output file
        """
        # Generate speech
        generator = self.pipeline(text, voice=self.voice, speed=speed)
        
        audio_chunks = []
        for i, (graphemes, phonemes, audio) in enumerate(generator):
            audio_chunks.append(audio)
        
        # Combine chunks
        final_audio = np.concatenate(audio_chunks)
        
        # Enhance if requested
        if enhance_audio:
            final_audio = self.enhance_audio(final_audio)
        
        # Save
        sf.write(output_file, final_audio, self.sample_rate)
        print(f"✅ Generated: {output_file}")
        
        return output_file
    
    def enhance_audio(self, audio):
        """
        Enhance audio quality using librosa
        
        - Normalizes volume
        - Removes silence
        - Applies noise reduction
        - Adds fade in/out
        """
        # Normalize
        audio = librosa.util.normalize(audio)
        
        # Trim silence (20dB threshold)
        audio, _ = librosa.effects.trim(audio, top_db=20)
        
        # Spectral noise reduction
        stft = librosa.stft(audio)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Simple noise gate
        noise_floor = np.percentile(magnitude, 10)
        magnitude[magnitude < noise_floor] = 0
        
        # Reconstruct
        enhanced_stft = magnitude * np.exp(1j * phase)
        audio = librosa.istft(enhanced_stft)
        
        # Add subtle fade (100ms)
        fade_samples = int(0.1 * self.sample_rate)
        audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
        audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        return audio
    
    def batch_generate(self, text_list, output_dir='outputs'):
        """Generate multiple audio files"""
        os.makedirs(output_dir, exist_ok=True)
        
        for i, text in enumerate(text_list):
            output_file = f"{output_dir}/audio_{i+1:03d}.wav"
            self.text_to_speech(text, output_file)
        
        print(f"✅ Generated {len(text_list)} files in {output_dir}")
    
    def process_script(self, script_file, output_file='complete_voiceover.wav'):
        """
        Process entire video script
        
        Reads script, splits by paragraphs, generates audio,
        combines with gaps
        """
        # Read script
        with open(script_file, 'r') as f:
            script = f.read()
        
        # Split into segments
        segments = [s.strip() for s in script.split('\n\n') if s.strip()]
        
        # Generate segments
        audio_segments = []
        gap = np.zeros(int(0.5 * self.sample_rate))  # 500ms gap
        
        for i, segment in enumerate(segments):
            print(f"Processing segment {i+1}/{len(segments)}...")
            
            generator = self.pipeline(segment, voice=self.voice)
            segment_audio = np.concatenate([a for _, _, a in generator])
            segment_audio = self.enhance_audio(segment_audio)
            
            audio_segments.append(segment_audio)
            if i < len(segments) - 1:  # No gap after last segment
                audio_segments.append(gap)
        
        # Combine all
        final_audio = np.concatenate(audio_segments)
        sf.write(output_file, final_audio, self.sample_rate)
        
        print(f"✅ Complete voiceover: {output_file}")
        return output_file


# Usage Examples
if __name__ == "__main__":
    # Example 1: Simple generation
    tts = YouTubeTTS(voice='am_michael')
    tts.text_to_speech(
        "Welcome to Aparsoft's YouTube channel",
        "intro.wav"
    )
    
    # Example 2: Process full script
    script = """
    Hi, I'm from Aparsoft, and today we're going to show you 
    how to deploy AI solutions in just 10 days.
    
    First, let's understand our Quick AI Solutions approach.
    
    Unlike traditional consultancy, we use pre-built modules.
    
    Subscribe for more AI tutorials!
    """
    
    with open('script.txt', 'w') as f:
        f.write(script)
    
    tts.process_script('script.txt', 'final_voiceover.wav')
```

---

## 🔌 MCP Server Setup

### What is MCP?

Model Context Protocol (MCP) is a standardized way for AI applications to interact with external tools and data sources. Our TTS MCP server allows Claude Desktop, Cursor, and other AI tools to generate speech on demand.

### MCP Server Implementation

Create `tts_mcp_server.py`:

```python
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio
from kokoro import KPipeline
import soundfile as sf
import numpy as np
import librosa
import asyncio

# Initialize MCP server
app = Server("aparsoft-tts-server")

# Initialize TTS pipeline
pipeline = KPipeline(lang_code='a')

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available TTS tools"""
    return [
        Tool(
            name="generate_speech",
            description="Generate high-quality speech from text using Kokoro TTS with audio enhancement",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to convert to speech"
                    },
                    "voice": {
                        "type": "string",
                        "description": "Voice ID: am_michael (default), bm_george, am_adam, af_bella",
                        "default": "am_michael"
                    },
                    "speed": {
                        "type": "number",
                        "description": "Speech speed (0.5-2.0)",
                        "default": 1.0,
                        "minimum": 0.5,
                        "maximum": 2.0
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Output filename (default: output.wav)",
                        "default": "output.wav"
                    },
                    "enhance": {
                        "type": "boolean",
                        "description": "Apply audio enhancement",
                        "default": True
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="list_voices",
            description="List all available voices",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    
    if name == "list_voices":
        voices = {
            "Male Voices": [
                "am_michael - Professional American male (recommended)",
                "bm_george - British male, formal",
                "am_adam - American male, younger"
            ],
            "Female Voices": [
                "af_bella - American female, warm",
                "af_heart - American female, expressive",
                "bf_emma - British female, professional"
            ]
        }
        
        result = "Available Voices:\n\n"
        for category, voice_list in voices.items():
            result += f"{category}:\n"
            for voice in voice_list:
                result += f"  - {voice}\n"
            result += "\n"
        
        return [TextContent(type="text", text=result)]
    
    elif name == "generate_speech":
        text = arguments["text"]
        voice = arguments.get("voice", "am_michael")
        speed = arguments.get("speed", 1.0)
        output_file = arguments.get("output_file", "output.wav")
        enhance = arguments.get("enhance", True)
        
        try:
            # Generate speech
            generator = pipeline(text, voice=voice, speed=speed)
            audio_chunks = []
            
            for _, _, audio in generator:
                audio_chunks.append(audio)
            
            final_audio = np.concatenate(audio_chunks)
            
            # Enhance if requested
            if enhance:
                # Normalize
                final_audio = librosa.util.normalize(final_audio)
                # Trim silence
                final_audio, _ = librosa.effects.trim(final_audio, top_db=20)
                # Add fade
                fade_samples = int(0.1 * 24000)
                final_audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
                final_audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            # Save
            sf.write(output_file, final_audio, 24000)
            
            duration = len(final_audio) / 24000
            
            return [TextContent(
                type="text",
                text=f"✅ Speech generated successfully!\n\nFile: {output_file}\nVoice: {voice}\nDuration: {duration:.1f}s\nEnhanced: {enhance}"
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error generating speech: {str(e)}"
            )]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### Configure MCP in Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%/Claude/claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "aparsoft-tts": {
      "command": "/path/to/tts_env/bin/python",
      "args": ["/path/to/tts_mcp_server.py"]
    }
  }
}
```

### Configure MCP in Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "aparsoft-tts": {
      "command": "/path/to/tts_env/bin/python",
      "args": ["/path/to/tts_mcp_server.py"]
    }
  }
}
```

### Using the MCP Server

Once configured, you can use it in Claude Desktop or Cursor:

```
"Can you generate speech for: 'Welcome to Aparsoft's channel' 
using the am_michael voice and save it as intro.wav?"
```

The AI will automatically call the MCP server tool to generate the audio!

---

## 🎨 Advanced Features

### 1. Voice Mixing

Create unique voices by mixing existing ones:

```python
import torch
from kokoro import KPipeline
import numpy as np
import soundfile as sf

def mix_voices(text, output_file='mixed.wav'):
    """Mix multiple voices for unique sound"""
    
    # Load voice packs
    voice1 = torch.load('voices/am_michael.pt')
    voice2 = torch.load('voices/bm_george.pt')
    
    # Mix (70% Michael, 30% George)
    mixed_voice = (voice1 * 0.7 + voice2 * 0.3) / 1.0
    
    # Generate with mixed voice
    pipeline = KPipeline(lang_code='a')
    generator = pipeline(text, voice=mixed_voice)
    
    audio = np.concatenate([a for _, _, a in generator])
    sf.write(output_file, audio, 24000)

# Usage
mix_voices("This is a custom mixed voice", "custom_voice.wav")
```

### 2. Advanced Audio Processing

```python
import librosa
import numpy as np
from scipy import signal

def advanced_enhancement(audio, sr=24000):
    """Advanced audio enhancement"""
    
    # 1. Normalize
    audio = librosa.util.normalize(audio)
    
    # 2. High-pass filter (remove low-frequency rumble)
    sos = signal.butter(10, 80, 'hp', fs=sr, output='sos')
    audio = signal.sosfilt(sos, audio)
    
    # 3. De-essing (reduce harsh 's' sounds)
    sos_deess = signal.butter(5, [4000, 8000], 'bandstop', fs=sr, output='sos')
    audio = signal.sosfilt(sos_deess, audio)
    
    # 4. Compression (even out volume)
    threshold = 0.3
    ratio = 3.0
    audio_abs = np.abs(audio)
    compressed = np.where(
        audio_abs > threshold,
        threshold + (audio_abs - threshold) / ratio,
        audio_abs
    )
    audio = np.sign(audio) * compressed
    
    # 5. Final normalization
    audio = librosa.util.normalize(audio)
    
    return audio
```

### 3. Segment-Based Video Production

```python
class VideoVoiceoverProducer:
    """Advanced video voiceover production"""
    
    def __init__(self, voice='am_michael'):
        self.tts = YouTubeTTS(voice=voice)
    
    def create_from_timestamps(self, script_with_timestamps, output_dir='segments'):
        """
        Process script with timestamps
        
        Format:
        [00:00] Welcome to our channel
        [00:05] In this video, we'll show you...
        [00:15] First, let's understand...
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Parse script
        segments = []
        for line in script_with_timestamps.split('\n'):
            if line.strip() and line.startswith('['):
                timestamp = line[1:6]  # Extract HH:MM
                text = line[8:].strip()  # Extract text
                segments.append((timestamp, text))
        
        # Generate audio for each segment
        for i, (timestamp, text) in enumerate(segments):
            output_file = f"{output_dir}/segment_{timestamp.replace(':', '_')}.wav"
            self.tts.text_to_speech(text, output_file)
            print(f"✅ Generated: {timestamp} - {output_file}")
        
        return segments

# Usage
producer = VideoVoiceoverProducer()
script = """
[00:00] Welcome to Aparsoft's YouTube channel
[00:05] Today we're showing you Quick AI Solutions
[00:10] Deploy in just 10 days
[00:15] Subscribe for more tutorials
"""
producer.create_from_timestamps(script)
```

### 4. Real-time Streaming (for live applications)

```python
import queue
import threading

class StreamingTTS:
    """Generate and stream audio in real-time"""
    
    def __init__(self):
        self.pipeline = KPipeline(lang_code='a')
        self.audio_queue = queue.Queue()
    
    def generate_stream(self, text, voice='am_michael'):
        """Generate audio chunks in real-time"""
        generator = self.pipeline(text, voice=voice)
        
        for _, _, audio in generator:
            self.audio_queue.put(audio)
        
        self.audio_queue.put(None)  # Signal end
    
    def play_stream(self):
        """Play audio as it's generated"""
        import sounddevice as sd
        
        while True:
            chunk = self.audio_queue.get()
            if chunk is None:
                break
            sd.play(chunk, 24000)
            sd.wait()

# Usage
streamer = StreamingTTS()

# Start generation in background
threading.Thread(
    target=streamer.generate_stream,
    args=("This is streaming speech", "am_michael")
).start()

# Play as it's generated
streamer.play_stream()
```

---

## 📚 API Reference

### YouTubeTTS Class

#### `__init__(voice='am_michael', lang_code='a')`

Initialize TTS system.

**Parameters:**
- `voice` (str): Voice ID
- `lang_code` (str): Language code ('a' = American, 'b' = British)

#### `text_to_speech(text, output_file='output.wav', speed=1.0, enhance_audio=True)`

Generate speech from text.

**Parameters:**
- `text` (str): Input text
- `output_file` (str): Output filename
- `speed` (float): Speech speed (0.5-2.0)
- `enhance_audio` (bool): Apply enhancement

**Returns:** Path to output file

#### `enhance_audio(audio)`

Enhance audio quality.

**Parameters:**
- `audio` (numpy.ndarray): Audio array

**Returns:** Enhanced audio array

#### `batch_generate(text_list, output_dir='outputs')`

Generate multiple audio files.

**Parameters:**
- `text_list` (list): List of text strings
- `output_dir` (str): Output directory

#### `process_script(script_file, output_file='complete_voiceover.wav')`

Process complete video script.

**Parameters:**
- `script_file` (str): Path to script file
- `output_file` (str): Output filename

**Returns:** Path to output file

---

## 📊 Model Comparison

| Model | Quality Score | Speed | Parameters | License | Best For |
|-------|--------------|-------|------------|---------|----------|
| **Kokoro-82M** | 44% (TTS Arena) | ⚡⚡⚡⚡ | 82M | Apache 2.0 | YouTube videos ⭐ |
| Parler-TTS Mini | High | ⚡⚡⚡ | 880M | Apache 2.0 | Controllable voice |
| Parler-TTS Large | Very High | ⚡⚡ | 2.3B | Apache 2.0 | Maximum quality |
| Chatterbox | High | ⚡⚡⚡⚡⚡ | 500M | Apache 2.0 | Fast generation |
| MMS | Good | ⚡⚡⚡ | Varies | CC-BY-NC 4.0 | Multilingual |

### Quality Metrics

Based on TTS Arena community voting (October 2025):

- **Kokoro-82M**: 44% win rate
- **Parler-TTS**: High naturalness, excellent controllability
- **Chatterbox**: 42% win rate, fastest inference

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **"ModuleNotFoundError: No module named 'kokoro'"**

```bash
# Solution: Install kokoro
pip install kokoro>=0.9.2

# Verify installation
python -c "from kokoro import KPipeline; print('✅ Success')"
```

#### 2. **"espeak-ng not found"**

```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng

# macOS
brew install espeak

# Windows: Download from http://espeak.sourceforge.net/
```

#### 3. **Audio quality issues**

```python
# Increase enhancement
tts = YouTubeTTS()
tts.text_to_speech(
    text="Your text",
    enhance_audio=True  # Make sure this is True
)

# Or use advanced enhancement
from youtube_tts import advanced_enhancement
enhanced = advanced_enhancement(audio)
```

#### 4. **"RuntimeError: No audio backend is available"**

```bash
# Install audio backend
pip install sounddevice

# On Ubuntu
sudo apt-get install portaudio19-dev python3-pyaudio

# On macOS
brew install portaudio
```

#### 5. **MCP server not connecting**

```bash
# Check Python path
which python

# Verify server runs
python tts_mcp_server.py

# Check config file
cat ~/.cursor/mcp.json
# or
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

#### 6. **Slow generation**

```python
# Use CUDA if available
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Or use faster model
tts = YouTubeTTS(voice='am_michael')  # Kokoro is already fast
```

### Performance Tips

1. **Batch Processing**: Process multiple segments together
2. **GPU Acceleration**: Use CUDA for faster processing
3. **Cache Voices**: Load voice models once, reuse
4. **Optimize Audio**: Use `enhance_audio=False` for faster generation (draft mode)

---

## 🎯 Production Workflow for Aparsoft YouTube

### Complete Video Production Pipeline

```python
# aparsoft_video_pipeline.py

from youtube_tts import YouTubeTTS
import os

class AparsoftVideoPipeline:
    """Complete pipeline for Aparsoft YouTube videos"""
    
    def __init__(self):
        self.tts = YouTubeTTS(voice='am_michael')
    
    def create_tutorial_voiceover(self, tutorial_title, script_sections):
        """
        Create voiceover for tutorial video
        
        Args:
            tutorial_title: Video title
            script_sections: Dict of {section_name: script_text}
        """
        output_dir = f"tutorials/{tutorial_title.replace(' ', '_')}"
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Generate intro
        intro_text = f"Welcome to Aparsoft. In this tutorial: {tutorial_title}"
        self.tts.text_to_speech(
            intro_text, 
            f"{output_dir}/00_intro.wav"
        )
        
        # 2. Generate sections
        for i, (section, text) in enumerate(script_sections.items(), 1):
            self.tts.text_to_speech(
                text,
                f"{output_dir}/{i:02d}_{section}.wav"
            )
        
        # 3. Generate outro
        outro_text = "Thanks for watching! Subscribe for more AI tutorials from Aparsoft."
        self.tts.text_to_speech(
            outro_text,
            f"{output_dir}/99_outro.wav"
        )
        
        print(f"✅ Complete voiceover ready in: {output_dir}")
        return output_dir

# Usage
pipeline = AparsoftVideoPipeline()

tutorial = pipeline.create_tutorial_voiceover(
    tutorial_title="Deploy Django AI Chatbot in 10 Days",
    script_sections={
        "setup": "First, let's set up our Django environment...",
        "ai_integration": "Next, we'll integrate the AI model...",
        "deployment": "Finally, we'll deploy to production..."
    }
)
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup

```bash
# Clone repo
git clone https://github.com/aparsoft/youtube-tts.git
cd youtube-tts

# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Format code
black .
```

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses

- **Kokoro-82M**: Apache License 2.0
- **Librosa**: ISC License
- **FastMCP**: MIT License

---

## 🙏 Acknowledgments

- **Kokoro Team** at hexgrad for the excellent TTS model
- **Anthropic** for Model Context Protocol
- **Hugging Face** for hosting models and community
- **Librosa developers** for audio processing tools

---

## 📞 Support & Contact

- **Email**: contact@aparsoft.com
- **Phone**: +91 8904064878
- **Website**: https://aparsoft.com
- **YouTube**: [Aparsoft Channel](https://youtube.com/@aparsoft)

---

## 🚀 What's Next?

- [ ] Add more voice customization options
- [ ] Implement voice cloning
- [ ] Add multi-language support
- [ ] Create web UI for non-technical users
- [ ] Integrate with video editing tools

---

## 📈 Project Stats

- ⭐ **Models Used**: Kokoro-82M (82M params, #1 on HF)
- 🎤 **Voices Available**: 50+ across 8 languages
- ⚡ **Generation Speed**: Real-time (1s audio = 0.5s generation)
- 💰 **Cost**: $0 (100% open-source)
- 📊 **Quality**: 44% win rate on TTS Arena

---

**Built with ❤️ by Aparsoft for the YouTube creator community**

---

*Last Updated: October 2025*