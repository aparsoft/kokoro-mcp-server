"""Complete YouTube video production workflow example."""

from pathlib import Path
from aparsoft_tts.core.engine import TTSEngine


def create_youtube_voiceover():
    """Complete workflow for creating a YouTube video voiceover."""

    print("🎬 YouTube Video Production Workflow")
    print("=" * 60)

    # Initialize engine with professional male voice
    engine = TTSEngine()

    # Define video script with segments
    video_sections = {
        "intro": """
            Hi, I'm from Aparsoft. In this tutorial, we're going to show you
            how to deploy production-ready AI chatbots in just 10 days.
        """,

        "hook": """
            Most companies spend 3 to 6 months on AI projects.
            But what if you could go from idea to deployment in 10 days?
        """,

        "section_1": """
            First, let's understand our Quick AI Solutions approach.
            We use pre-built modules and proven frameworks instead of building from scratch.
        """,

        "section_2": """
            Here's how it works. We start with your requirements,
            select the appropriate AI models, and configure them for your use case.
        """,

        "section_3": """
            Next, we integrate the AI with your existing systems using our
            standardized deployment pipeline.
        """,

        "demo": """
            Let me show you a real example. This chatbot was deployed for a
            healthcare company in just 8 days.
        """,

        "call_to_action": """
            If you want to deploy AI solutions quickly, visit aparsoft.com
            or call us at +91 8904064878.
        """,

        "outro": """
            Thanks for watching! Subscribe to our channel for more AI tutorials,
            and hit the bell icon for notifications. See you in the next video!
        """
    }

    # Create output directory
    output_dir = Path("youtube_voiceover")
    output_dir.mkdir(exist_ok=True)

    # Generate individual segments
    print("\n📝 Generating voiceover segments...")
    segment_paths = []

    for i, (name, text) in enumerate(video_sections.items(), 1):
        print(f"  {i}. Generating {name}...")

        output_file = output_dir / f"{i:02d}_{name}.wav"
        engine.generate(
            text=text.strip(),
            output_path=output_file,
            voice="am_michael",
            speed=1.0
        )

        segment_paths.append(output_file)

    # Create complete script file
    full_script = "\n\n".join(text.strip() for text in video_sections.values())
    script_path = output_dir / "full_script.txt"
    script_path.write_text(full_script)

    # Generate complete voiceover
    print("\n🎙️  Generating complete voiceover...")
    complete_path = engine.process_script(
        script_path=script_path,
        output_path=output_dir / "complete_voiceover.wav",
        gap_duration=0.5
    )

    # Summary
    print("\n✅ Production Complete!")
    print("=" * 60)
    print(f"Segments created: {len(segment_paths)}")
    print(f"Output directory: {output_dir}/")
    print(f"Complete voiceover: {complete_path}")
    print("\n📂 Files:")
    for path in sorted(output_dir.glob("*.wav")):
        size_kb = path.stat().st_size / 1024
        print(f"  • {path.name} ({size_kb:.1f} KB)")

    print("\n🎬 Next steps:")
    print("  1. Import complete_voiceover.wav into your video editor")
    print("  2. Sync with visuals")
    print("  3. Add music and sound effects")
    print("  4. Export and upload to YouTube!")
    print("=" * 60)


if __name__ == "__main__":
    create_youtube_voiceover()
