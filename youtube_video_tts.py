# youtube_video_tts.py
import os
from pathlib import Path
from kokoro import KPipeline
import soundfile as sf
import librosa
import numpy as np


class YouTubeVoiceoverGenerator:
    def __init__(self):
        self.pipeline = KPipeline(lang_code="a")
        self.voice = "am_michael"  # Professional male voice

    def process_script(self, script_file, output_dir="voiceovers"):
        """
        Process entire video script
        """
        os.makedirs(output_dir, exist_ok=True)

        # Read script
        with open(script_file, "r") as f:
            script = f.read()

        # Split into segments (by paragraph or timestamp)
        segments = script.split("\n\n")

        audio_files = []
        for i, segment in enumerate(segments):
            if segment.strip():
                output_file = f"{output_dir}/segment_{i+1:03d}.wav"
                self.generate_segment(segment, output_file)
                audio_files.append(output_file)

        # Combine all segments
        self.combine_audio_files(audio_files, f"{output_dir}/complete_voiceover.wav")

        return f"{output_dir}/complete_voiceover.wav"

    def generate_segment(self, text, output_file, speed=1.0):
        """Generate single segment"""
        generator = self.pipeline(text, voice=self.voice, speed=speed)

        audio_chunks = []
        for _, _, audio in generator:
            audio_chunks.append(audio)

        final_audio = np.concatenate(audio_chunks)

        # Enhance
        final_audio = self.enhance_for_video(final_audio)

        sf.write(output_file, final_audio, 24000)

    def enhance_for_video(self, audio):
        """Optimize audio for video"""
        # Normalize
        audio = librosa.util.normalize(audio)

        # Trim silence
        audio, _ = librosa.effects.trim(audio, top_db=25)

        # Add subtle fade in/out
        fade_duration = int(0.1 * 24000)  # 100ms fade
        audio[:fade_duration] *= np.linspace(0, 1, fade_duration)
        audio[-fade_duration:] *= np.linspace(1, 0, fade_duration)

        return audio

    def combine_audio_files(self, audio_files, output_file, gap_duration=0.5):
        """Combine multiple audio files with gaps"""
        combined = []
        gap = np.zeros(int(gap_duration * 24000))

        for audio_file in audio_files:
            audio, sr = librosa.load(audio_file, sr=24000)
            combined.append(audio)
            combined.append(gap)

        final = np.concatenate(combined)
        sf.write(output_file, final, 24000)


# Usage for your YouTube videos
if __name__ == "__main__":
    generator = YouTubeVoiceoverGenerator()

    # Your video script
    script = """
    Hi, I'm from Aparsoft, and in this video, we'll show you how to deploy 
    AI solutions in just 10 days.
    
    First, let's understand our Quick AI Solutions approach.
    
    Unlike traditional consultancy that takes months, we use pre-built modules.
    """

    # Save script
    with open("script.txt", "w") as f:
        f.write(script)

    # Generate complete voiceover
    final_audio = generator.process_script("script.txt")
    print(f"✅ Complete voiceover: {final_audio}")
