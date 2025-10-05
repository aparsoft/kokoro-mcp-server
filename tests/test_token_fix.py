#!/usr/bin/env python3
"""Test script to verify the token counting fix."""

from aparsoft_tts import TTSEngine

# Initialize engine
print("Initializing TTS engine...")
engine = TTSEngine()

# Test token counting
test_text = "This is a test sentence to verify token counting works correctly."
print(f"\nTest text: {test_text}")

# Count tokens
token_count = engine._count_tokens(test_text, lang_code='a')
print(f"Token count: {token_count}")

# Generate a short audio to verify everything works
print("\nGenerating test audio...")
output = engine.generate(
    text="Token counting is now fixed!",
    output_path="test_token_fix.wav"
)

print(f"✅ Success! Audio generated: {output}")
print("\nThe import error should be fixed now!")
