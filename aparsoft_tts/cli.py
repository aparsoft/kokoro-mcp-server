# aparsoft_tts/cli.py

"""Command-line interface for Aparsoft TTS."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from aparsoft_tts.core.engine import ALL_VOICES, TTSEngine
from aparsoft_tts.utils.exceptions import AparsoftTTSError
from aparsoft_tts.utils.logging import setup_logging

app = typer.Typer(
    name="aparsoft-tts",
    help="Comprehensive Text-to-Speech for YouTube Videos",
    add_completion=False,
)

console = Console()


@app.callback()
def callback():
    """Initialize the CLI application."""
    setup_logging()


@app.command()
def generate(
    text: str = typer.Argument(..., help="Text to convert to speech"),
    output: Path = typer.Option("output.wav", "--output", "-o", help="Output file path"),
    voice: str = typer.Option(
        "am_michael",
        "--voice",
        "-v",
        help=f"Voice to use ({', '.join(ALL_VOICES[:3])}...)",
    ),
    speed: float = typer.Option(
        1.0, "--speed", "-s", min=0.5, max=2.0, help="Speech speed (0.5-2.0)"
    ),
    no_enhance: bool = typer.Option(False, "--no-enhance", help="Disable audio enhancement"),
):
    """Generate speech from text.

    Example:
        aparsoft-tts generate "Hello world" -o hello.wav
        aparsoft-tts generate "Welcome" -v af_bella -s 1.2
    """
    try:
        console.print(f"[bold blue]Generating speech...[/bold blue]")

        engine = TTSEngine()
        result = engine.generate(
            text=text,
            output_path=output,
            voice=voice,
            speed=speed,
            enhance=not no_enhance,
        )

        console.print(f"[bold green]✅ Success![/bold green]")
        console.print(f"Output: {result}")

    except AparsoftTTSError as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    texts: list[str] = typer.Argument(..., help="Texts to convert"),
    output_dir: Path = typer.Option("outputs", "--output-dir", "-d", help="Output directory"),
    voice: str = typer.Option("am_michael", "--voice", "-v", help="Voice to use"),
    speed: float = typer.Option(1.0, "--speed", "-s", help="Speech speed"),
):
    """Generate multiple audio files.

    Example:
        aparsoft-tts batch "Intro" "Body" "Outro" -d segments/
    """
    try:
        console.print(f"[bold blue]Batch processing {len(texts)} texts...[/bold blue]")

        engine = TTSEngine()
        paths = engine.batch_generate(texts=texts, output_dir=output_dir, voice=voice, speed=speed)

        console.print(f"[bold green]✅ Generated {len(paths)} files[/bold green]")
        for path in paths:
            console.print(f"  • {path}")

    except AparsoftTTSError as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def script(
    script_path: Path = typer.Argument(..., help="Path to script file", exists=True),
    output: Path = typer.Option("voiceover.wav", "--output", "-o", help="Output file path"),
    voice: str = typer.Option("am_michael", "--voice", "-v", help="Voice to use"),
    speed: float = typer.Option(1.0, "--speed", "-s", help="Speech speed"),
    gap: float = typer.Option(0.5, "--gap", "-g", help="Gap between segments (seconds)"),
):
    """Process a complete video script.

    Example:
        aparsoft-tts script video_script.txt -o final.wav
        aparsoft-tts script script.txt -v bm_george -s 0.9 -g 0.7
    """
    try:
        console.print(f"[bold blue]Processing script: {script_path}[/bold blue]")

        engine = TTSEngine()
        result = engine.process_script(
            script_path=script_path,
            output_path=output,
            gap_duration=gap,
            voice=voice,
            speed=speed,
        )

        console.print(f"[bold green]✅ Script processed![/bold green]")
        console.print(f"Output: {result}")

    except AparsoftTTSError as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def voices():
    """List all available voices.

    Example:
        aparsoft-tts voices
    """
    voices_dict = TTSEngine.list_voices()

    table = Table(title="Available Voices", show_header=True, header_style="bold magenta")
    table.add_column("Voice ID", style="cyan")
    table.add_column("Gender", style="green")
    table.add_column("Accent", style="yellow")
    table.add_column("Recommended", style="red")

    for voice in voices_dict["male"]:
        accent = "American" if voice.startswith("am_") else "British"
        recommended = "⭐" if voice == "am_michael" else ""
        table.add_row(voice, "Male", accent, recommended)

    for voice in voices_dict["female"]:
        accent = "American" if voice.startswith("af_") else "British"
        table.add_row(voice, "Female", accent, "")

    console.print(table)
    console.print("\n[bold]Recommended for YouTube:[/bold] am_michael")


@app.command()
def version():
    """Show version information."""
    console.print("[bold]Aparsoft TTS[/bold] v1.0.0")
    console.print("Comprehensive Text-to-Speech for YouTube Videos")


if __name__ == "__main__":
    app()
