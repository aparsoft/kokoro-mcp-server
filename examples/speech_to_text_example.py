"""Example: Speech-to-Text using OpenAI Whisper

This example demonstrates how to use the speech-to-text functionality
added to the Aparsoft TTS toolkit.

Includes 6 examples:
1. Basic transcription
2. Save transcription to file
3. Timestamped transcription
4. Model comparison
5. Multi-voice podcast generation + transcription
6. Batch transcription

Requirements:
    pip install -e ".[stt]"
    sudo apt-get install ffmpeg  # or brew install ffmpeg on macOS

Usage:
    python examples/speech_to_text_example.py
"""

from pathlib import Path
from aparsoft_tts import TTSEngine
from aparsoft_tts.utils.audio import transcribe_audio


def example_1_basic_transcription():
    """Example 1: Basic audio transcription."""
    print("\n" + "=" * 70)
    print("Example 1: Basic Audio Transcription")
    print("=" * 70)

    # First, generate some sample audio using TTS
    print("\n1. Generating sample audio with TTS...")
    engine = TTSEngine()
    sample_text = "Hello, this is a test of the speech to text functionality."
    
    audio_file = "examples/outputs/sample_speech.wav"
    Path("examples/outputs").mkdir(parents=True, exist_ok=True)
    
    engine.generate(sample_text, audio_file)
    print(f"   ✓ Generated: {audio_file}")

    # Now transcribe it back
    print("\n2. Transcribing the audio back to text...")
    result = transcribe_audio(audio_file, model_size="base")
    
    print(f"   ✓ Transcribed!")
    print(f"\nOriginal text: {sample_text}")
    print(f"Transcribed:   {result['text']}")
    print(f"Language:      {result['language']}")
    print(f"Segments:      {len(result['segments'])}")


def example_2_save_to_file():
    """Example 2: Transcribe and save to file."""
    print("\n" + "=" * 70)
    print("Example 2: Transcribe and Save to File")
    print("=" * 70)

    # Generate a longer sample
    print("\n1. Generating longer sample audio...")
    engine = TTSEngine()
    long_text = """
    Welcome to our tutorial series on artificial intelligence.
    In this episode, we'll explore the fundamentals of machine learning.
    We'll cover supervised learning, unsupervised learning, and reinforcement learning.
    Stay tuned for more exciting content!
    """
    
    audio_file = "examples/outputs/tutorial.wav"
    transcript_file = "examples/outputs/tutorial_transcript.txt"
    
    engine.generate(long_text.strip(), audio_file)
    print(f"   ✓ Generated: {audio_file}")

    # Transcribe and save
    print("\n2. Transcribing to file...")
    result = transcribe_audio(
        audio_path=audio_file,
        output_path=transcript_file,
        model_size="base"
    )
    
    print(f"   ✓ Transcription saved to: {transcript_file}")
    print(f"   Text length: {len(result['text'])} characters")
    print(f"   Word count: ~{len(result['text'].split())} words")
    
    # Show the saved content
    print(f"\n3. Content of {transcript_file}:")
    print("-" * 70)
    with open(transcript_file, 'r') as f:
        print(f.read())
    print("-" * 70)


def example_3_timestamped_transcription():
    """Example 3: Get timestamped transcription segments."""
    print("\n" + "=" * 70)
    print("Example 3: Timestamped Transcription")
    print("=" * 70)

    # Generate audio with pauses
    print("\n1. Generating sample with multiple segments...")
    engine = TTSEngine()
    
    # Use paragraph breaks for natural pauses
    paragraphs = [
        "First, let's discuss the introduction.",
        "Next, we'll cover the main points.",
        "Finally, we'll wrap up with conclusions."
    ]
    
    audio_file = "examples/outputs/segmented_speech.wav"
    
    # Generate each paragraph separately and combine
    from aparsoft_tts.utils.audio import combine_audio_segments, save_audio
    
    segments = []
    for para in paragraphs:
        audio = engine.generate(para)
        segments.append(audio)
    
    # Combine with gaps
    combined = combine_audio_segments(segments, gap_duration=0.5)
    save_audio(combined, audio_file)
    print(f"   ✓ Generated: {audio_file}")

    # Transcribe with timestamps
    print("\n2. Transcribing with timestamps...")
    result = transcribe_audio(audio_file, model_size="base")
    
    print(f"   ✓ Transcribed {len(result['segments'])} segments")
    
    print("\n3. Timestamped segments:")
    print("-" * 70)
    for i, segment in enumerate(result['segments'], 1):
        start = segment['start']
        end = segment['end']
        text = segment['text'].strip()
        duration = end - start
        print(f"Segment {i}: [{start:6.2f}s → {end:6.2f}s] ({duration:5.2f}s)")
        print(f"  \"{text}\"")
    print("-" * 70)


def example_4_model_comparison():
    """Example 4: Compare different Whisper models."""
    print("\n" + "=" * 70)
    print("Example 4: Compare Whisper Model Sizes")
    print("=" * 70)

    # Generate test audio
    print("\n1. Generating test audio...")
    engine = TTSEngine()
    test_text = "The quick brown fox jumps over the lazy dog."
    audio_file = "examples/outputs/fox_test.wav"
    
    engine.generate(test_text, audio_file)
    print(f"   ✓ Generated: {audio_file}")

    # Test different models
    models = ["tiny", "base"]  # Start with small models
    
    print("\n2. Comparing models...")
    print("-" * 70)
    
    import time
    for model in models:
        print(f"\nModel: {model}")
        
        start_time = time.time()
        result = transcribe_audio(audio_file, model_size=model)
        elapsed = time.time() - start_time
        
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Text: {result['text']}")
        print(f"  Match: {'✓' if 'quick brown fox' in result['text'].lower() else '✗'}")
    
    print("-" * 70)
    print("\nNote: Try 'medium' or 'large' for even better accuracy!")


def example_5_podcast_generation_and_transcription():
    """Example 5: Generate multi-voice podcast and transcribe it."""
    print("\n" + "=" * 70)
    print("Example 5: Podcast Generation + Transcription")
    print("=" * 70)

    # Generate a multi-voice podcast
    print("\n1. Generating multi-voice podcast...")
    engine = TTSEngine()
    
    podcast_file = "examples/outputs/podcast_episode.wav"
    
    # Create podcast segments with different voices
    segments = [
        {"text": "Welcome to Tech Talk, I'm your host Michael.", "voice": "am_michael", "speed": 1.0},
        {"text": "And I'm Sarah, thanks for joining us today.", "voice": "af_sarah", "speed": 0.95},
        {"text": "Today we're discussing artificial intelligence and machine learning.", "voice": "am_michael", "speed": 1.0},
        {"text": "It's a fascinating topic with so many real-world applications.", "voice": "af_sarah", "speed": 0.95},
        {"text": "That's right. Thanks for listening, see you next week!", "voice": "am_michael", "speed": 1.0},
    ]
    
    # Generate each segment
    from aparsoft_tts.utils.audio import combine_audio_segments, save_audio
    
    audio_segments = []
    for i, seg in enumerate(segments, 1):
        print(f"   Generating segment {i}/{len(segments)} ({seg['voice']})...")
        audio = engine.generate(
            text=seg["text"],
            voice=seg["voice"],
            speed=seg["speed"]
        )
        audio_segments.append(audio)
    
    # Combine segments with gaps
    combined = combine_audio_segments(
        audio_segments,
        gap_duration=0.6,
        sample_rate=24000
    )
    
    save_audio(combined, podcast_file, sample_rate=24000)
    print(f"   ✓ Podcast saved: {podcast_file}")

    # Transcribe the podcast
    print("\n2. Transcribing podcast to create transcript...")
    transcript_file = "examples/outputs/podcast_transcript.txt"
    
    result = transcribe_audio(
        audio_path=podcast_file,
        output_path=transcript_file,
        model_size="base"
    )
    
    print(f"   ✓ Transcript saved: {transcript_file}")
    print(f"   Text length: {len(result['text'])} characters")
    print(f"   Detected language: {result['language']}")
    
    # Show timestamped segments
    print("\n3. Timestamped podcast segments:")
    print("-" * 70)
    for i, segment in enumerate(result['segments'], 1):
        start = segment['start']
        end = segment['end']
        text = segment['text'].strip()
        print(f"[{start:5.1f}s - {end:5.1f}s] {text}")
    print("-" * 70)
    
    print("\n4. Full transcript:")
    print("-" * 70)
    print(result['text'])
    print("-" * 70)


def example_6_batch_transcription():
    """Example 6: Batch transcribe multiple files."""
    print("\n" + "=" * 70)
    print("Example 6: Batch Transcription")
    print("=" * 70)

    # Generate multiple audio files
    print("\n1. Generating multiple audio files...")
    engine = TTSEngine()
    
    files_to_create = {
        "intro": "Welcome to our channel!",
        "body": "Today we're discussing artificial intelligence.",
        "outro": "Thanks for watching, see you next time!"
    }
    
    audio_dir = Path("examples/outputs/batch")
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    for name, text in files_to_create.items():
        audio_file = audio_dir / f"{name}.wav"
        engine.generate(text, audio_file)
        print(f"   ✓ Created: {audio_file.name}")

    # Batch transcribe
    print("\n2. Batch transcribing all files...")
    audio_files = list(audio_dir.glob("*.wav"))
    
    for audio_file in audio_files:
        transcript_file = audio_file.with_suffix(".txt")
        
        result = transcribe_audio(
            audio_path=audio_file,
            output_path=transcript_file,
            model_size="base"
        )
        
        print(f"   ✓ {audio_file.name} → {transcript_file.name}")
        print(f"      {result['text'][:50]}...")

    print(f"\n3. All transcripts saved to: {audio_dir}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Speech-to-Text Examples for Aparsoft TTS")
    print("=" * 70)
    print("\nThese examples demonstrate the new speech-to-text functionality")
    print("using OpenAI Whisper integrated into the Aparsoft TTS toolkit.")
    
    try:
        # Check if Whisper is installed
        import whisper
        print("\n✓ OpenAI Whisper is installed")
    except ImportError:
        print("\n✗ OpenAI Whisper is NOT installed!")
        print("\nPlease install it with:")
        print("  pip install openai-whisper")
        print("\nAlso ensure ffmpeg is installed:")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  macOS: brew install ffmpeg")
        return

    try:
        example_1_basic_transcription()
        example_2_save_to_file()
        example_3_timestamped_transcription()
        example_4_model_comparison()
        example_5_podcast_generation_and_transcription()
        example_6_batch_transcription()
        
        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)
        print("\nGenerated files are in: examples/outputs/")
        print("\nFor more information, see:")
        print("  - SPEECH_TO_TEXT.md (full documentation)")
        print("  - STT_QUICK_REFERENCE.md (quick reference)")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        print("\nPlease ensure:")
        print("  1. OpenAI Whisper is installed: pip install openai-whisper")
        print("  2. FFmpeg is installed on your system")
        print("  3. You have enough disk space and RAM")


if __name__ == "__main__":
    main()
