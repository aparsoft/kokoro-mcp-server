# tts_mcp_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio
from kokoro import KPipeline
import soundfile as sf
import numpy as np
import librosa

app = Server("kokoro-tts-server")

# Initialize TTS pipeline
pipeline = KPipeline(lang_code="a")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available TTS tools"""
    return [
        Tool(
            name="generate_speech",
            description="Generate speech from text using Kokoro TTS",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to convert to speech",
                    },
                    "voice": {
                        "type": "string",
                        "description": "Voice to use (am_michael, bm_george, am_adam)",
                        "default": "am_michael",
                    },
                    "speed": {
                        "type": "number",
                        "description": "Speech speed (0.5-2.0)",
                        "default": 1.0,
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Output filename",
                        "default": "output.wav",
                    },
                },
                "required": ["text"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    if name == "generate_speech":
        text = arguments["text"]
        voice = arguments.get("voice", "am_michael")
        speed = arguments.get("speed", 1.0)
        output_file = arguments.get("output_file", "output.wav")

        # Generate speech
        generator = pipeline(text, voice=voice, speed=speed)
        audio_chunks = []

        for _, _, audio in generator:
            audio_chunks.append(audio)

        final_audio = np.concatenate(audio_chunks)

        # Enhance with librosa
        final_audio = librosa.util.normalize(final_audio)
        final_audio, _ = librosa.effects.trim(final_audio, top_db=20)

        # Save
        sf.write(output_file, final_audio, 24000)

        return [
            TextContent(
                type="text", text=f"✅ Speech generated successfully: {output_file}"
            )
        ]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
