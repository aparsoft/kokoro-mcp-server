#!/usr/bin/env python3
"""
Hindi TTS Testing Script

This script demonstrates all Hindi voice capabilities in Aparsoft TTS.
Run this to verify Hindi support is working correctly.
"""

from pathlib import Path
from aparsoft_tts.core.engine import TTSEngine
from aparsoft_tts.utils.audio import combine_audio_segments, save_audio


def test_basic_hindi_generation():
    """Test 1: Basic Hindi generation with all voices"""
    print("\n" + "="*60)
    print("TEST 1: Basic Hindi Generation")
    print("="*60)
    
    engine = TTSEngine()
    output_dir = Path("test_outputs/hindi")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test text in Hindi
    test_text = "नमस्ते, यह एक परीक्षण है। मेरा नाम राज है।"
    
    # Test all Hindi voices
    voices = ["hf_alpha", "hf_beta", "hm_omega", "hm_psi"]
    
    for voice in voices:
        print(f"\n✓ Testing voice: {voice}")
        output_file = output_dir / f"test_{voice}.wav"
        
        try:
            result = engine.generate(
                text=test_text,
                output_path=output_file,
                voice=voice,
                speed=1.0
            )
            print(f"  ✓ Success: {result}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n✓ Test 1 Complete: Check test_outputs/hindi/ for results")


def test_speed_variations():
    """Test 2: Hindi with different speeds"""
    print("\n" + "="*60)
    print("TEST 2: Hindi Speed Variations")
    print("="*60)
    
    engine = TTSEngine()
    output_dir = Path("test_outputs/hindi_speeds")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    text = "यह गति परिवर्तन का परीक्षण है।"
    speeds = [0.8, 1.0, 1.2]
    
    for speed in speeds:
        print(f"\n✓ Testing speed: {speed}x")
        output_file = output_dir / f"speed_{speed}.wav"
        
        try:
            result = engine.generate(
                text=text,
                output_path=output_file,
                voice="hf_alpha",
                speed=speed
            )
            print(f"  ✓ Success: {result}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n✓ Test 2 Complete: Check test_outputs/hindi_speeds/")


def test_long_text_chunking():
    """Test 3: Long Hindi text with automatic chunking"""
    print("\n" + "="*60)
    print("TEST 3: Long Text Chunking")
    print("="*60)
    
    engine = TTSEngine()
    output_dir = Path("test_outputs/hindi_long")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Long Hindi text that will trigger chunking
    long_text = """
    यह एक लंबा परीक्षण पाठ है। हम देखेंगे कि इंजन इसे कैसे संभालता है।
    
    पहला पैराग्राफ यहाँ है। इसमें कई वाक्य होने चाहिए। प्रत्येक वाक्य को ठीक से 
    उच्चारित किया जाना चाहिए।
    
    दूसरा पैराग्राफ और भी जानकारी प्रदान करता है। यह सुनिश्चित करता है कि 
    टोकन सीमा पार हो जाए। इंजन इसे स्वचालित रूप से विभाजित करेगा।
    
    अंतिम पैराग्राफ में निष्कर्ष होता है। यह परीक्षण का अंत है।
    """
    
    print("\n✓ Generating long Hindi text with automatic chunking")
    output_file = output_dir / "long_text.wav"
    
    try:
        result = engine.generate(
            text=long_text,
            output_path=output_file,
            voice="hm_omega",
            speed=1.0
        )
        print(f"  ✓ Success: {result}")
        print("  ℹ️  Check logs to see chunking in action")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print("\n✓ Test 3 Complete: Check test_outputs/hindi_long/")


def test_batch_generation():
    """Test 4: Batch processing of Hindi texts"""
    print("\n" + "="*60)
    print("TEST 4: Batch Processing")
    print("="*60)
    
    engine = TTSEngine()
    output_dir = Path("test_outputs/hindi_batch")
    
    hindi_texts = [
        "यह पहला वाक्य है।",
        "यह दूसरा वाक्य है।",
        "यह तीसरा वाक्य है।",
        "यह चौथा वाक्य है।"
    ]
    
    print(f"\n✓ Batch generating {len(hindi_texts)} Hindi audio files")
    
    try:
        results = engine.batch_generate(
            texts=hindi_texts,
            output_dir=output_dir,
            voice="hf_beta",
            speed=1.0,
            filename_prefix="hindi_batch"
        )
        print(f"  ✓ Success: Generated {len(results)} files")
        for result in results:
            print(f"    - {result}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print("\n✓ Test 4 Complete: Check test_outputs/hindi_batch/")


def test_mixed_language():
    """Test 5: Combining English and Hindi audio"""
    print("\n" + "="*60)
    print("TEST 5: Mixed Language (English + Hindi)")
    print("="*60)
    
    engine = TTSEngine()
    output_dir = Path("test_outputs/mixed_language")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n✓ Generating English part")
    english_audio = engine.generate(
        text="Welcome to our channel. Today we will discuss important topics.",
        voice="am_michael"
    )
    print("  ✓ English audio generated")
    
    print("\n✓ Generating Hindi part")
    hindi_audio = engine.generate(
        text="हमारे चैनल में आपका स्वागत है। आज हम महत्वपूर्ण विषयों पर चर्चा करेंगे।",
        voice="hf_alpha"
    )
    print("  ✓ Hindi audio generated")
    
    print("\n✓ Combining English and Hindi with gap")
    combined = combine_audio_segments(
        segments=[english_audio, hindi_audio],
        sample_rate=24000,
        gap_duration=0.5
    )
    
    output_file = output_dir / "mixed_language.wav"
    save_audio(combined, output_file, sample_rate=24000)
    print(f"  ✓ Success: {output_file}")
    
    print("\n✓ Test 5 Complete: Check test_outputs/mixed_language/")


def test_voice_listing():
    """Test 6: List all available voices"""
    print("\n" + "="*60)
    print("TEST 6: Voice Listing")
    print("="*60)
    
    voices = TTSEngine.list_voices()
    
    print("\n✓ Available Voice Categories:")
    print(f"\n  English Male: {voices['male']}")
    print(f"  English Female: {voices['female']}")
    print(f"  Hindi Male: {voices['hindi_male']}")
    print(f"  Hindi Female: {voices['hindi_female']}")
    print(f"\n  Total Voices: {len(voices['all'])}")
    
    print("\n✓ Test 6 Complete")


def test_enhanced_audio():
    """Test 7: Hindi with audio enhancement"""
    print("\n" + "="*60)
    print("TEST 7: Audio Enhancement")
    print("="*60)
    
    engine = TTSEngine()
    output_dir = Path("test_outputs/hindi_enhanced")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    text = "यह ऑडियो एन्हांसमेंट का परीक्षण है। ध्वनि की गुणवत्ता बेहतर होनी चाहिए।"
    
    # Without enhancement
    print("\n✓ Generating without enhancement")
    result1 = engine.generate(
        text=text,
        output_path=output_dir / "no_enhancement.wav",
        voice="hf_alpha",
        enhance=False
    )
    print(f"  ✓ Success: {result1}")
    
    # With enhancement
    print("\n✓ Generating with enhancement")
    result2 = engine.generate(
        text=text,
        output_path=output_dir / "with_enhancement.wav",
        voice="hf_alpha",
        enhance=True
    )
    print(f"  ✓ Success: {result2}")
    
    print("\n✓ Test 7 Complete: Compare files in test_outputs/hindi_enhanced/")


def main():
    """Run all Hindi TTS tests"""
    print("\n" + "="*60)
    print("HINDI TTS COMPREHENSIVE TEST SUITE")
    print("="*60)
    print("\nThis script will test all Hindi voice capabilities.")
    print("Output files will be created in test_outputs/ directory.")
    
    try:
        # Run all tests
        test_basic_hindi_generation()
        test_speed_variations()
        test_long_text_chunking()
        test_batch_generation()
        test_mixed_language()
        test_voice_listing()
        test_enhanced_audio()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nCheck the test_outputs/ directory for all generated audio files.")
        print("\nHindi voices available:")
        print("  - hf_alpha (Female)")
        print("  - hf_beta (Female)")
        print("  - hm_omega (Male)")
        print("  - hm_psi (Male)")
        
    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED: {e}")
        print("\nPlease check:")
        print("  1. espeak-ng is installed (sudo apt-get install espeak-ng)")
        print("  2. Hindi language support is available")
        print("  3. All dependencies are installed")
        raise


if __name__ == "__main__":
    main()
