"""Basic usage examples for Aparsoft TTS."""

from pathlib import Path
from aparsoft_tts.core.engine import TTSEngine
from aparsoft_tts.config import TTSConfig


# Example 1: Simple text-to-speech
def basic_example():
    """Generate simple speech."""
    print("Example 1: Basic TTS")

    engine = TTSEngine()
    engine.generate(text="Welcome to Aparsoft's YouTube channel", output_path="example_output.wav")
    print("✅ Generated: example_output.wav\n")


# Example 2: Custom voice and speed
def custom_voice_example():
    """Use different voice and speed."""
    print("Example 2: Custom voice and speed")

    engine = TTSEngine()
    engine.generate(
        text="This is British George speaking faster",
        output_path="example_george.wav",
        voice="bm_george",
        speed=1.3,
    )
    print("✅ Generated: example_george.wav\n")


# Example 3: Batch processing
def batch_example():
    """Generate multiple files."""
    print("Example 3: Batch processing")

    engine = TTSEngine()
    texts = [
        "Welcome to the video",
        "In this tutorial we'll cover AI deployment",
        "Don't forget to subscribe",
    ]

    paths = engine.batch_generate(texts=texts, output_dir="example_batch/", voice="am_michael")

    print(f"✅ Generated {len(paths)} files in example_batch/\n")


# Example 4: Process a full script
def script_example():
    """Process a complete video script."""
    print("Example 4: Process full script")

    # Create sample script
    script = """
Hi, I'm from Aparsoft, and in this video we'll show you how to deploy AI chatbots in just 10 days.

First, let's understand what makes our Quick AI Solutions different from traditional consultancy.

Unlike projects that take 3 to 6 months, we use pre-built modules and proven frameworks.

Thanks for watching! Subscribe for more AI tutorials.
    """

    script_path = Path("example_script.txt")
    script_path.write_text(script.strip())

    engine = TTSEngine()
    engine.process_script(
        script_path=script_path, output_path="example_complete.wav", gap_duration=0.5
    )

    print("✅ Generated: example_complete.wav\n")


# Example 5: Custom configuration
def config_example():
    """Use custom configuration."""
    print("Example 5: Custom configuration")

    config = TTSConfig(
        voice="af_bella",  # Female voice
        speed=0.9,  # Slightly slower
        enhance_audio=True,
        fade_duration=0.2,  # Longer fade
    )

    engine = TTSEngine(config=config)
    engine.generate(text="This example uses custom configuration", output_path="example_config.wav")

    print("✅ Generated: example_config.wav\n")


# Example 6: Streaming generation
def streaming_example():
    """Generate and process audio in chunks."""
    print("Example 6: Streaming generation")

    engine = TTSEngine()
    chunks = []
    stream_text = """

Hi, I'm from Aparsoft, and in this video we'll show you how to deploy AI chatbots in just 10 days.

First, let's understand what makes our Quick AI Solutions different from traditional consultancy.

Second, we'll explore our modular architecture that allows rapid deployment.

Third, we'll demonstrate a live deployment example.

Unlike projects that take 3 to 6 months, we use pre-built modules and proven frameworks.

Thanks for watching! Subscribe for more AI tutorials.

"""

    for chunk in engine.generate_stream(stream_text):
        chunks.append(chunk)
        print(f"  Received chunk: {len(chunk)} samples")

    print(f"✅ Total chunks: {len(chunks)}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Aparsoft TTS - Usage Examples")
    print("=" * 60 + "\n")

    # basic_example()
    # custom_voice_example()
    # batch_example()
    # script_example()
    # config_example()
    streaming_example()

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)
