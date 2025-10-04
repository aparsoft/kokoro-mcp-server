# advanced_tts.py
from kokoro import KPipeline, KPipeline
import numpy as np
import soundfile as sf


def mix_voices(text, voices=["am_michael", "bm_george"], weights=[0.7, 0.3]):
    """
    Mix multiple voices for unique sound
    """
    pipeline = KPipeline(lang_code="a")

    # Load voice packs
    import torch

    voicepack1 = torch.load(f"voices/{voices[0]}.pt")
    voicepack2 = torch.load(f"voices/{voices[1]}.pt")

    # Mix voices
    mixed_voice = (voicepack1 * weights[0] + voicepack2 * weights[1]) / sum(weights)

    # Generate with mixed voice
    generator = pipeline(text, voice=mixed_voice)

    audio_chunks = []
    for _, _, audio in generator:
        audio_chunks.append(audio)

    return np.concatenate(audio_chunks)
