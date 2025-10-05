"""Test script to isolate the am_michael cutoff issue - IMPROVED VERSION."""

from aparsoft_tts import TTSEngine
from aparsoft_tts.utils.audio import save_audio
import numpy as np

text = "Welcome to the tutorial on Aparsoft TTS"

print("=" * 60)
print("VOICE CUTOFF DIAGNOSTIC TEST")
print("=" * 60)

# Initialize engine
engine = TTSEngine()

# Test 1: am_michael WITHOUT any enhancement (RAW Kokoro output)
print("\nTest 1: am_michael - RAW Kokoro output (NO enhancement)")
audio_michael_raw = engine.generate(
    text,
    voice="am_michael",
    enhance=False,
)
print(
    f"  ✓ Raw audio length: {len(audio_michael_raw)} samples ({len(audio_michael_raw)/24000:.2f}s)"
)

# Test 2: bm_george WITHOUT enhancement (RAW Kokoro output)
print("\nTest 2: bm_george - RAW Kokoro output (NO enhancement)")
audio_george_raw = engine.generate(text, voice="bm_george", enhance=False)
print(f"  ✓ Raw audio length: {len(audio_george_raw)} samples ({len(audio_george_raw)/24000:.2f}s)")

# Test 3: am_michael WITH enhancement (to see if enhancement is the problem)
print("\nTest 3: am_michael - WITH enhancement (our audio pipeline)")
audio_michael_enhanced = engine.generate(text, voice="am_michael", enhance=True)
print(
    f"  ✓ Enhanced audio length: {len(audio_michael_enhanced)} samples ({len(audio_michael_enhanced)/24000:.2f}s)"
)

# Test 4: bm_george WITH enhancement
print("\nTest 4: bm_george - WITH enhancement (our audio pipeline)")
audio_george_enhanced = engine.generate(text, voice="bm_george", enhance=True)
print(
    f"  ✓ Enhanced audio length: {len(audio_george_enhanced)} samples ({len(audio_george_enhanced)/24000:.2f}s)"
)

# Save all files for comparison
save_audio(audio_michael_raw, "output/1_am_michael_RAW.wav", 24000)
save_audio(audio_george_raw, "output/2_bm_george_RAW.wav", 24000)
save_audio(audio_michael_enhanced, "output/3_am_michael_ENHANCED.wav", 24000)
save_audio(audio_george_enhanced, "output/4_bm_george_ENHANCED.wav", 24000)

# Analysis
print("\n" + "=" * 60)
print("ANALYSIS")
print("=" * 60)

print("\nRAW Audio Comparison (Kokoro output only):")
print(f"  Length difference: {abs(len(audio_michael_raw) - len(audio_george_raw))} samples")
print(f"  Time difference: {abs(len(audio_michael_raw) - len(audio_george_raw))/24000:.3f}s")

print("\nENHANCED Audio Comparison (with our pipeline):")
print(
    f"  Length difference: {abs(len(audio_michael_enhanced) - len(audio_george_enhanced))} samples"
)
print(
    f"  Time difference: {abs(len(audio_michael_enhanced) - len(audio_george_enhanced))/24000:.3f}s"
)

print("\nam_michael: RAW vs ENHANCED:")
print(f"  Lost in enhancement: {len(audio_michael_raw) - len(audio_michael_enhanced)} samples")
print(f"  Time lost: {(len(audio_michael_raw) - len(audio_michael_enhanced))/24000:.3f}s")

print("\n" + "=" * 60)
print("FILES SAVED - Listen to them in order:")
print("=" * 60)
print("\n1. output/1_am_michael_RAW.wav     (Kokoro raw output)")
print("2. output/2_bm_george_RAW.wav      (Kokoro raw output)")
print("3. output/3_am_michael_ENHANCED.wav (After our audio pipeline)")
print("4. output/4_bm_george_ENHANCED.wav  (After our audio pipeline)")

print("\n" + "=" * 60)
print("DIAGNOSIS GUIDE:")
print("=" * 60)
print("\nIf am_michael cuts off in file #1 (RAW):")
print("  → Problem not in our code")
print("  → NOT our code")
print("\nIf am_michael is fine in #1 but cuts off in #3 (ENHANCED):")
print("  → Problem is in our audio enhancement (trim_db, margin, etc.)")
print("  → We can fix by adjusting audio.py parameters")
print("\nIf both am_michael files (#1 and #3) are fine:")
print("  → Problem might be elsewhere in your workflow")
print("=" * 60)
