import soundfile as sf
from kokoro import KPipeline
import librosa
import numpy as np


class YouTubeTTS:
    def __init__(self, voice="am_michael", lang_code="a"):
        """
        Initialize TTS with male voice
        voice options: 'am_michael', 'bm_george', 'am_adam' (male voices)
        lang_code: 'a' for American English, 'b' for British English
        """
        self.pipeline = KPipeline(lang_code=lang_code)
        self.voice = voice

    def text_to_speech(self, text, output_file="output.wav", speed=1.0, enhance_audio=True):
        """
        Convert text to speech with optional audio enhancement
        """
        # Generate speech
        generator = self.pipeline(text, voice=self.voice, speed=speed)

        audio_chunks = []
        for i, (gs, ps, audio) in enumerate(generator):
            audio_chunks.append(audio)

        # Combine all audio chunks
        final_audio = np.concatenate(audio_chunks)

        # Optional: Enhance audio quality using librosa
        if enhance_audio:
            final_audio = self.enhance_audio(final_audio)

        # Save to file
        sf.write(output_file, final_audio, 24000)
        print(f"✅ Audio saved to: {output_file}")

        return output_file

    def enhance_audio(self, audio, sample_rate=24000):
        """
        Enhance audio quality using librosa
        """
        # Normalize audio
        audio = librosa.util.normalize(audio)

        # Remove silence from beginning and end
        audio, _ = librosa.effects.trim(audio, top_db=20)

        # Apply subtle noise reduction (optional)
        # This uses spectral gating
        stft = librosa.stft(audio)
        magnitude = np.abs(stft)
        phase = np.angle(stft)

        # Simple noise gate
        noise_floor = np.percentile(magnitude, 10)
        magnitude[magnitude < noise_floor] = 0

        # Reconstruct
        enhanced_stft = magnitude * np.exp(1j * phase)
        audio = librosa.istft(enhanced_stft)

        return audio

    def batch_generate(self, text_list, output_dir="outputs"):
        """
        Generate multiple audio files
        """
        import os

        os.makedirs(output_dir, exist_ok=True)

        for i, text in enumerate(text_list):
            output_file = f"{output_dir}/audio_{i+1}.wav"
            self.text_to_speech(text, output_file)

        print(f"✅ Generated {len(text_list)} audio files")


# Usage Example
if __name__ == "__main__":
    tts = YouTubeTTS(voice="am_michael")  # Professional male voice

    script = """
    Welcome to Aparsoft's YouTube channel. 
    In this video, we'll explore how to deploy AI solutions in just 10 days.
    Let's get started!

    Here is a quick overview of what you'll learn:
    1. Understanding AI fundamentals
    2. Setting up your development environment
    3. Building your first AI model
    4. Testing and deploying your AI solution
    5. Best practices and tips for success

    Don't forget to like, subscribe, and hit the notification bell for more exciting content!
    See you in the next video!
    """

    tts.text_to_speech(script, "youtube_intro.wav", speed=1.0)
