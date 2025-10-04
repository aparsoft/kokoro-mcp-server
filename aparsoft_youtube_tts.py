# aparsoft_youtube_tts.py
from kokoro import KPipeline
import soundfile as sf
import numpy as np
import librosa


class AparsoftTTS:
    def __init__(self):
        self.pipeline = KPipeline(lang_code="a")
        self.voice = "am_michael"  # Professional, clear male voice

    def create_video_voiceover(self, script, output="voiceover.wav"):
        """One-command voiceover generation"""
        generator = self.pipeline(script, voice=self.voice, speed=1.05)

        audio = np.concatenate([a for _, _, a in generator])
        audio = librosa.util.normalize(audio)
        audio, _ = librosa.effects.trim(audio, top_db=20)

        sf.write(output, audio, 24000)
        return output


# USAGE
tts = AparsoftTTS()
tts.create_video_voiceover("Your script here", "my_video_voice.wav")
