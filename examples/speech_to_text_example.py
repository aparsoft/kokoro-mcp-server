"""Example: Speech-to-Text using faster-whisper (Enhanced)

This example demonstrates the enhanced speech-to-text functionality
using faster-whisper (4x faster than openai-whisper!) in the Aparsoft TTS toolkit.

NEW FEATURES WITH FASTER-WHISPER:
✅ 4x faster transcription with same accuracy
✅ Lower memory usage
✅ 8-bit quantization for even better performance
✅ Built-in VAD (Voice Activity Detection) to filter silence
✅ Word-level timestamps
✅ GPU acceleration support
✅ Automatic device selection

Includes 8 examples:
1. Basic transcription (faster-whisper vs openai-whisper comparison)
2. Save transcription to file
3. Word-level timestamps (NEW!)
4. Model and compute type comparison (NEW!)
5. VAD filtering demonstration (NEW!)
6. Multi-voice podcast generation + transcription
7. Batch transcription
8. GPU vs CPU performance comparison (NEW!)

Requirements:
    pip install faster-whisper  # Recommended (4x faster!)
    # or
    pip install openai-whisper  # Fallback option

    # For GPU acceleration (optional but recommended):
    # CUDA 12 + cuDNN 9 libraries

Usage:
    python examples/speech_to_text_example.py
"""

from pathlib import Path
from aparsoft_tts import TTSEngine
from aparsoft_tts.utils.audio import transcribe_audio
import time


def example_1_basic_transcription_comparison():
    """Example 1: Compare faster-whisper vs openai-whisper."""
    print("\n" + "=" * 70)
    print("Example 1: faster-whisper vs openai-whisper Comparison")
    print("=" * 70)

    # Generate sample audio
    print("\n1. Generating sample audio with TTS...")
    engine = TTSEngine()
    sample_text = "Hello, this is a test of the faster whisper speech to text functionality."

    audio_file = "examples/outputs/sample_speech.wav"
    Path("examples/outputs").mkdir(parents=True, exist_ok=True)

    engine.generate(sample_text, audio_file)
    print(f"   ✓ Generated: {audio_file}")

    # Test with faster-whisper (default)
    print("\n2. Transcribing with faster-whisper (4x faster!)...")
    start_time = time.time()
    result_faster = transcribe_audio(
        audio_file, model_size="base", use_faster_whisper=True  # Default
    )
    faster_time = time.time() - start_time

    print(f"   ✓ Transcribed in {faster_time:.2f}s")
    print(f"   Text: {result_faster['text']}")
    print(
        f"   Language: {result_faster['language']} ({result_faster.get('language_probability', 0):.1%} confidence)"
    )

    # Test with openai-whisper for comparison
    print("\n3. Transcribing with openai-whisper (for comparison)...")
    try:
        start_time = time.time()
        result_openai = transcribe_audio(audio_file, model_size="base", use_faster_whisper=False)
        openai_time = time.time() - start_time

        print(f"   ✓ Transcribed in {openai_time:.2f}s")
        print(f"   Text: {result_openai['text']}")

        speedup = openai_time / faster_time
        print(f"\n⚡ faster-whisper is {speedup:.1f}x faster!")
    except ImportError:
        print("   ⚠ openai-whisper not installed (comparison skipped)")
        print("   💡 Install with: pip install openai-whisper")


def example_2_save_to_file():
    """Example 2: Transcribe and save to file with VAD filtering."""
    print("\n" + "=" * 70)
    print("Example 2: Transcribe and Save with VAD Filtering")
    print("=" * 70)

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

    # Transcribe with VAD filtering (removes silence automatically)
    print("\n2. Transcribing with VAD filtering...")
    result = transcribe_audio(
        audio_path=audio_file,
        output_path=transcript_file,
        model_size="base",
        vad_filter=True,  # Filter silence (default: True)
        device="auto",  # Auto-select CPU/GPU
    )

    print(f"   ✓ Transcription saved to: {transcript_file}")
    print(f"   Text length: {len(result['text'])} characters")
    print(f"   Word count: ~{len(result['text'].split())} words")
    print(f"   Segments: {len(result['segments'])} (silence filtered)")

    print(f"\n3. Content of {transcript_file}:")
    print("-" * 70)
    print(result["text"])
    print("-" * 70)


def example_3_word_timestamps():
    """Example 3: Word-level timestamps (NEW!)."""
    print("\n" + "=" * 70)
    print("Example 3: Word-Level Timestamps (NEW!)")
    print("=" * 70)

    print("\n1. Generating sample audio...")
    engine = TTSEngine()
    text = (
        "Artificial intelligence is transforming the world with machine learning and deep learning."
    )

    audio_file = "examples/outputs/word_timestamps.wav"
    engine.generate(text, audio_file)
    print(f"   ✓ Generated: {audio_file}")

    # Transcribe with word-level timestamps
    print("\n2. Transcribing with word-level timestamps...")
    result = transcribe_audio(
        audio_file, model_size="base", word_timestamps=True  # Enable word-level timestamps
    )

    print(f"   ✓ Transcribed!")

    print("\n3. Word-level timestamps:")
    print("-" * 70)
    for seg in result["segments"]:
        print(f"\nSegment {seg['id']} [{seg['start']:.2f}s - {seg['end']:.2f}s]:")
        if "words" in seg:
            for word in seg["words"]:
                print(
                    f"  [{word['start']:6.2f}s - {word['end']:6.2f}s] {word['word']:20s} (prob: {word['probability']:.2%})"
                )
    print("-" * 70)


def example_4_model_and_compute_comparison():
    """Example 4: Compare models and compute types (NEW!)."""
    print("\n" + "=" * 70)
    print("Example 4: Model Size & Compute Type Comparison")
    print("=" * 70)

    print("\n1. Generating test audio...")
    engine = TTSEngine()
    test_text = (
        "The quick brown fox jumps over the lazy dog while learning artificial intelligence."
    )
    audio_file = "examples/outputs/fox_test.wav"

    engine.generate(test_text, audio_file)
    print(f"   ✓ Generated: {audio_file}")

    # Test different configurations
    configs = [
        {"name": "Tiny (int8)", "model": "tiny", "compute": "int8"},
        {"name": "Base (int8)", "model": "base", "compute": "int8"},
        {"name": "Small (int8)", "model": "small", "compute": "int8"},
    ]

    print("\n2. Comparing different models...")
    print("-" * 70)

    for config in configs:
        print(f"\n{config['name']}:")

        start_time = time.time()
        result = transcribe_audio(
            audio_file, model_size=config["model"], compute_type=config["compute"]
        )
        elapsed = time.time() - start_time

        print(f"  Time: {elapsed:.2f}s")
        print(f"  Text: {result['text']}")
        print(f"  Language: {result['language']} ({result.get('language_probability', 0):.1%})")

    print("-" * 70)
    print("\n💡 Tip: Use 'large-v3' or 'turbo' for best accuracy!")
    print("💡 Tip: Use GPU with 'float16' for maximum speed!")


def example_5_vad_filtering_demo():
    """Example 5: VAD filtering demonstration (NEW!)."""
    print("\n" + "=" * 70)
    print("Example 5: VAD (Voice Activity Detection) Filtering")
    print("=" * 70)

    print("\n1. Generating audio with pauses...")
    engine = TTSEngine()

    # Generate segments with gaps
    segments_text = [
        "First segment.",
        "Second segment after a pause.",
        "Third segment with more content.",
    ]

    from aparsoft_tts.utils.audio import combine_audio_segments, save_audio

    segments = []
    for text in segments_text:
        audio = engine.generate(text)
        segments.append(audio)

    # Combine with longer gaps
    audio_file = "examples/outputs/vad_test.wav"
    combined = combine_audio_segments(segments, gap_duration=1.5)
    save_audio(combined, audio_file)
    print(f"   ✓ Generated: {audio_file} (with 1.5s gaps)")

    # Transcribe WITHOUT VAD
    print("\n2. Transcribing WITHOUT VAD filtering...")
    result_no_vad = transcribe_audio(audio_file, vad_filter=False)  # Disable VAD
    print(f"   Segments: {len(result_no_vad['segments'])}")
    print(f"   Text: {result_no_vad['text']}")

    # Transcribe WITH VAD
    print("\n3. Transcribing WITH VAD filtering...")
    result_with_vad = transcribe_audio(audio_file, vad_filter=True)  # Enable VAD (default)
    print(f"   Segments: {len(result_with_vad['segments'])}")
    print(f"   Text: {result_with_vad['text']}")

    print(
        f"\n✅ VAD filtered {len(result_no_vad['segments']) - len(result_with_vad['segments'])} silence segments!"
    )


def example_6_podcast_with_faster_whisper():
    """Example 6: Multi-voice podcast with faster-whisper."""
    print("\n" + "=" * 70)
    print("Example 6: Multi-Voice Podcast + faster-whisper Transcription")
    print("=" * 70)

    print("\n1. Generating multi-voice podcast...")
    engine = TTSEngine()

    podcast_file = "examples/outputs/podcast_episode.wav"

    segments = [
        {
            "text": "Welcome to Tech Talk, I'm your host Michael.",
            "voice": "am_michael",
            "speed": 1.0,
        },
        {"text": "And I'm Sarah, thanks for joining us today.", "voice": "af_sarah", "speed": 0.95},
        {
            "text": "Today we're discussing artificial intelligence and machine learning.",
            "voice": "am_michael",
            "speed": 1.0,
        },
        {
            "text": "It's a fascinating topic with so many real-world applications.",
            "voice": "af_sarah",
            "speed": 0.95,
        },
        {
            "text": "That's right. Thanks for listening, see you next week!",
            "voice": "am_michael",
            "speed": 1.0,
        },
    ]

    from aparsoft_tts.utils.audio import combine_audio_segments, save_audio

    audio_segments = []
    for i, seg in enumerate(segments, 1):
        print(f"   Generating segment {i}/{len(segments)} ({seg['voice']})...")
        audio = engine.generate(text=seg["text"], voice=seg["voice"], speed=seg["speed"])
        audio_segments.append(audio)

    combined = combine_audio_segments(audio_segments, gap_duration=0.6)
    save_audio(combined, podcast_file, sample_rate=24000)
    print(f"   ✓ Podcast saved: {podcast_file}")

    # Transcribe with faster-whisper
    print("\n2. Transcribing podcast with faster-whisper...")
    transcript_file = "examples/outputs/podcast_transcript.txt"

    start_time = time.time()
    result = transcribe_audio(
        audio_path=podcast_file,
        output_path=transcript_file,
        model_size="base",
        vad_filter=True,
        device="auto",
    )
    elapsed = time.time() - start_time

    print(f"   ✓ Transcribed in {elapsed:.2f}s")
    print(f"   Transcript saved: {transcript_file}")
    print(f"   Language: {result['language']} ({result.get('language_probability', 0):.1%})")

    print("\n3. Timestamped segments:")
    print("-" * 70)
    for seg in result["segments"]:
        print(f"[{seg['start']:5.1f}s - {seg['end']:5.1f}s] {seg['text']}")
    print("-" * 70)


def example_7_batch_transcription():
    """Example 7: Batch transcribe multiple files."""
    print("\n" + "=" * 70)
    print("Example 7: Batch Transcription with faster-whisper")
    print("=" * 70)

    print("\n1. Generating multiple audio files...")
    engine = TTSEngine()

    files_to_create = {
        "intro": "Welcome to our channel!",
        "body": "Today we're discussing the benefits of faster whisper for transcription.",
        "outro": "Thanks for watching, subscribe for more content!",
    }

    audio_dir = Path("examples/outputs/batch")
    audio_dir.mkdir(parents=True, exist_ok=True)

    for name, text in files_to_create.items():
        audio_file = audio_dir / f"{name}.wav"
        engine.generate(text, audio_file)
        print(f"   ✓ Created: {audio_file.name}")

    # Batch transcribe
    print("\n2. Batch transcribing with faster-whisper...")
    audio_files = list(audio_dir.glob("*.wav"))

    start_time = time.time()
    for audio_file in audio_files:
        transcript_file = audio_file.with_suffix(".txt")

        result = transcribe_audio(
            audio_path=audio_file, output_path=transcript_file, model_size="base", vad_filter=True
        )

        print(f"   ✓ {audio_file.name} → {transcript_file.name}")
        print(f"      {result['text'][:60]}...")

    elapsed = time.time() - start_time
    print(f"\n⚡ Transcribed {len(audio_files)} files in {elapsed:.2f}s")
    print(f"📂 All transcripts saved to: {audio_dir}")


def example_8_gpu_vs_cpu():
    """Example 8: GPU vs CPU performance comparison (NEW!)."""
    print("\n" + "=" * 70)
    print("Example 8: GPU vs CPU Performance Comparison")
    print("=" * 70)

    print("\n1. Generating test audio...")
    engine = TTSEngine()
    text = "Artificial intelligence and machine learning are revolutionizing technology across industries."
    audio_file = "examples/outputs/gpu_cpu_test.wav"

    engine.generate(text, audio_file)
    print(f"   ✓ Generated: {audio_file}")

    # Check CUDA availability
    try:
        import torch

        has_cuda = torch.cuda.is_available()
        if has_cuda:
            print(f"   ✅ CUDA available: {torch.cuda.get_device_name(0)}")
        else:
            print("   ⚠️  CUDA not available")
    except ImportError:
        has_cuda = False
        print("   ⚠️  PyTorch not installed, can't check CUDA")

    # Test CPU
    print("\n2. Testing CPU (int8)...")
    start_time = time.time()
    result_cpu = transcribe_audio(audio_file, model_size="base", device="cpu", compute_type="int8")
    cpu_time = time.time() - start_time
    print(f"   ⏱️  CPU Time: {cpu_time:.2f}s")
    print(f"   Text: {result_cpu['text']}")

    # Test GPU if available
    if has_cuda:
        print("\n3. Testing GPU (float16)...")
        start_time = time.time()
        result_gpu = transcribe_audio(
            audio_file, model_size="base", device="cuda", compute_type="float16"
        )
        gpu_time = time.time() - start_time
        print(f"   ⏱️  GPU Time: {gpu_time:.2f}s")
        print(f"   Text: {result_gpu['text']}")

        speedup = cpu_time / gpu_time
        print(f"\n⚡ GPU is {speedup:.1f}x faster than CPU!")
    else:
        print("\n3. GPU test skipped (CUDA not available)")
        print("   💡 Install PyTorch with CUDA for GPU acceleration")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("🚀 faster-whisper Examples for Aparsoft TTS")
    print("=" * 70)
    print("\nThese examples demonstrate faster-whisper (4x faster than openai-whisper!)")
    print("with the same accuracy, lower memory usage, and additional features.")

    try:
        # Check if faster-whisper is installed
        import faster_whisper

        print("\n✅ faster-whisper is installed")
    except ImportError:
        print("\n❌ faster-whisper is NOT installed!")
        print("\nPlease install it with:")
        print("  pip install faster-whisper")
        print("\nFor GPU acceleration, also ensure CUDA 12 + cuDNN 9 are installed.")
        return

    try:
        example_1_basic_transcription_comparison()
        example_2_save_to_file()
        example_3_word_timestamps()
        example_4_model_and_compute_comparison()
        example_5_vad_filtering_demo()
        example_6_podcast_with_faster_whisper()
        example_7_batch_transcription()
        example_8_gpu_vs_cpu()

        print("\n" + "=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70)
        print("\n📂 Generated files are in: examples/outputs/")
        print("\n📚 Key takeaways:")
        print("  • faster-whisper is 4x faster with same accuracy")
        print("  • Use VAD filtering to remove silence")
        print("  • Word-level timestamps available")
        print("  • GPU acceleration for even better performance")
        print("  • int8 quantization reduces memory usage")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("\nPlease ensure:")
        print("  1. faster-whisper is installed: pip install faster-whisper")
        print("  2. You have enough disk space and RAM")
        print("  3. For GPU: CUDA 12 + cuDNN 9 are installed")


if __name__ == "__main__":
    main()
