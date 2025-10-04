# parler_tts_solution.py
import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf


class ParlerTTSGenerator:
    def __init__(self, model_name="parler-tts/parler-tts-mini-v1"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = ParlerTTSForConditionalGeneration.from_pretrained(model_name).to(
            self.device
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def generate_speech(self, text, output_file="output.wav", voice_description=None):
        """
        Generate speech with voice description control
        """
        if voice_description is None:
            voice_description = (
                "A male speaker delivers clear and professional speech "
                "with moderate speed and natural intonation. "
                "The recording is of very high quality."
            )

        input_ids = self.tokenizer(voice_description, return_tensors="pt").input_ids.to(
            self.device
        )

        prompt_input_ids = self.tokenizer(text, return_tensors="pt").input_ids.to(
            self.device
        )

        generation = self.model.generate(
            input_ids=input_ids, prompt_input_ids=prompt_input_ids
        )

        audio_arr = generation.cpu().numpy().squeeze()
        sf.write(output_file, audio_arr, self.model.config.sampling_rate)

        return output_file


# Usage
tts = ParlerTTSGenerator()
tts.generate_speech(
    "Welcome to our channel",
    voice_description="A professional male voice with clear articulation",
)
