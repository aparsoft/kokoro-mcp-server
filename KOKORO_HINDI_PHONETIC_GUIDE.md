# Kokoro Hindi TTS - Phonetic Devanagari Guide

## 🎯 Overview

This guide explains the **optimal text format for Kokoro Hindi TTS voices** (hf_alpha, hm_omega, etc.) to achieve the best quality output.

**📅 Last Updated:** October 18, 2025  
**🔄 Update Type:** MCP Server Tools & Prompts Enhanced with Phonetic Devanagari Best Practices

## 🔥 The Golden Rules

### Rule #1: Use Phonetic Devanagari for English Words

**❌ DON'T** write English words in Latin script:
```
"बच्चों, आज हम MATHEMATICS सीखेंगे। SCIENCE भी IMPORTANT है।"
``` 

**✅ DO** write English words phonetically in Devanagari:
```
"बच्चों, आज हम मैथमेटिक्स सीखेंगे. साइंस भी एमपॉउरटेंट है."
```

### Rule #2: Use English Full Stop (.) NOT Hindi Danda (।)

**❌ DON्T** use Hindi danda (।):
```
"बच्चों, आज हम मैथमेटिक्स सीखेंगे। यह एमपॉउरटेंट है।"
```

**✅ DO** use English full stop (.):
```
"बच्चों, आज हम मैथमेटिक्स सीखेंगे. यह एमपॉउरटेंट है."
```

## 📝 Common English → Phonetic Devanagari Conversions

| English | Phonetic Devanagari |
|---------|---------------------|
| MATHEMATICS | मैथमेटिक्स |
| SCIENCE | साइंस |
| TECHNOLOGY | टेक्नोलॉजी |
| COMPUTER | कंप्यूटर |
| PROGRAMMING | प्रोग्रामिंग |
| IMPORTANT | एमपॉउरटेंट |
| EDUCATION | एजुकेशन |
| UNIVERSITY | यूनिवर्सिटी |
| ENGLISH | इंग्लिश |
| HISTORY | हिस्ट्री |
| GEOGRAPHY | जियोग्राफी |
| PHYSICS | फिजिक्स |
| CHEMISTRY | केमिस्ट्री |
| BIOLOGY | बायोलॉजी |
| ECONOMICS | इकोनॉमिक्स |
| PSYCHOLOGY | साइकोलॉजी |
| PHILOSOPHY | फिलॉसफी |
| LITERATURE | लिटरेचर |
| ALGEBRA | अल्जेब्रा |
| GEOMETRY | जियोमेट्री |
| CALCULUS | कैलकुलस |
| STATISTICS | स्टेटिस्टिक्स |
| INTERNET | इंटरनेट |
| WEBSITE | वेबसाइट |
| APPLICATION | एप्लीकेशन |
| SOFTWARE | सॉफ्टवेयर |
| HARDWARE | हार्डवेयर |
| DATABASE | डेटाबेस |
| NETWORK | नेटवर्क |
| SERVER | सर्वर |
| ALGORITHM | अल्गोरिदम |
| FUNCTION | फंक्शन |
| VARIABLE | वेरिएबल |
| PARAMETER | पैरामीटर |
| INTERFACE | इंटरफेस |
| MODULE | मॉड्यूल |
| LIBRARY | लाइब्रेरी |
| FRAMEWORK | फ्रेमवर्क |

## 🎓 Complete Example: Educational Tutorial

### ❌ WRONG Format (Raw English + Hindi Danda)
```
"नमस्ते बच्चों। आज हम COMPUTER SCIENCE सीखेंगे। PROGRAMMING बहुत IMPORTANT है। 
PYTHON एक POWERFUL LANGUAGE है। हम VARIABLES और FUNCTIONS सीखेंगे।"
```

### ✅ CORRECT Format (Phonetic Devanagari + English Full Stop)
```
"नमस्ते बच्चों. आज हम कंप्यूटर साइंस सीखेंगे. प्रोग्रामिंग बहुत एमपॉउरटेंट है. 
पायथन एक पावरफुल लैंग्वेज है. हम वेरिएबल्स और फंक्शंस सीखेंगे."
```

## 🔬 Why Does This Work?

**Kokoro's Hindi voice models were trained on:**
1. **Phonetic Devanagari text** - English words written in Hindi script
2. **English punctuation patterns** - Using (.) for sentence boundaries

This training approach allows the model to:
- Pronounce English technical terms naturally in a Hindi context
- Maintain proper rhythm and pacing with familiar punctuation
- Avoid awkward pauses or mispronunciations

## 🚀 Usage in MCP Tools

All MCP tools (`generate_speech`, `batch_generate`, `process_script`, `generate_podcast`) now include guidance for phonetic Devanagari usage when using Kokoro Hindi voices.

### Example: Generate Speech
```python
await generate_speech(GenerateSpeechRequest(
    text="बच्चों, आज हम मैथमेटिक्स सीखेंगे. अल्जेब्रा बहुत इंटरेस्टिंग है.",
    voice="hf_alpha",
    engine="kokoro",
    output_file="hindi_tutorial.wav"
))
```

### Example: Generate Podcast
```python
await generate_podcast(GeneratePodcastRequest(
    segments=[
        PodcastSegment(
            text="नमस्ते. आज हम टेक्नोलॉजी के बारे में बात करेंगे.",
            voice="hf_alpha",
            speed=1.0
        ),
        PodcastSegment(
            text="आर्टिफिशियल इंटेलिजेंस बहुत एमपॉउरटेंट है.",
            voice="hm_omega",
            speed=1.1
        )
    ],
    engine="kokoro",
    output_path="tech_podcast.wav"
))
```

## 📋 Quick Checklist

Before processing Hindi text with Kokoro:

- [ ] All English words converted to phonetic Devanagari
- [ ] All sentence endings use (.) not (।)
- [ ] No mixing of (.) and (।)
- [ ] No raw English words in Latin script
- [ ] Sentences are 5-15 words for natural flow
- [ ] Technical abbreviations written phonetically (AI → आर्टिफिशियल इंटेलिजेंस)

## 🎯 Result

Following these practices will give you:
- ✅ Natural-sounding Hindi speech
- ✅ Proper pronunciation of English technical terms
- ✅ Correct rhythm and pacing
- ✅ Professional audio quality
- ✅ No awkward pauses or mispronunciations

## � What Was Updated in MCP Server?

### Files Modified:

#### 1. `aparsoft_tts/mcp_server/mcp_tools.py`
All tools now include phonetic Devanagari guidance:
- ✅ `generate_speech` - Updated Hindi language note
- ✅ `batch_generate` - Added phonetic examples
- ✅ `process_script` - Enhanced with conversion tips
- ✅ `generate_podcast` - Comprehensive phonetic guide

**Key Change:**
```python
🇮🇳 IMPORTANT - KOKORO HINDI LANGUAGE BEST PRACTICES:
✅ USE PHONETIC HINDI DEVANAGARI with English full stops (.)
- Write English words phonetically: MATHEMATICS → मैथमेटिक्स
- Use English full stops (.) instead of Hindi danda (।)
```

#### 2. `aparsoft_tts/mcp_server/mcp_prompts.py`
Enhanced `hindi_script_optimizer` prompt with:
- ✅ "Golden Rule" section (2 critical rules)
- ✅ Common phonetic conversions reference
- ✅ Updated examples with phonetic Devanagari
- ✅ Enhanced mistake detection (raw English detection)
- ✅ Comprehensive quick checklist

#### 3. New Demo Script: `examples/kokoro_hindi_phonetic_demo.py`
Run this to hear the quality difference:
```bash
python examples/kokoro_hindi_phonetic_demo.py
```

Generates:
- `wrong_format.wav` - Raw English + Hindi danda (poor quality)
- `correct_format.wav` - Phonetic Devanagari + English full stop (best quality)
- `educational_tutorial.wav` - Complete example

## 🎯 Impact on Claude's Behavior

When Claude uses MCP tools for Hindi TTS, it will now **automatically**:

1. **Convert English words to phonetic Devanagari:**
   - "MATHEMATICS" → "मैथमेटिक्स"
   - "SCIENCE" → "साइंस"
   - "TECHNOLOGY" → "टेक्नोलॉजी"

2. **Use correct punctuation:**
   - English full stops (.) ✅
   - NOT Hindi danda (।) ❌

3. **Follow best practices:**
   - Short sentences (5-15 words)
   - Consistent formatting
   - Natural flow

## 📊 Benefits

### For Users:
- ✅ Better audio quality from Kokoro Hindi voices
- ✅ Natural pronunciation of English technical terms
- ✅ Proper rhythm and pacing
- ✅ Professional-sounding output

### For Claude:
- ✅ Clear guidance on text formatting
- ✅ Comprehensive examples to follow
- ✅ Automatic best practice enforcement
- ✅ Reduced trial-and-error

## �📚 Related Documentation

- `HINDI_TTS_GUIDE.md` - Complete Hindi TTS setup and usage
- `PODCAST_GUIDELINES.md` - Podcast creation best practices
- `MCP_QUICK_REF.md` - MCP server quick reference
- MCP Tools: All tools updated with phonetic Devanagari guidance
- MCP Prompts: `hindi_script_optimizer` - Interactive optimization guide

---

**Last Updated:** October 18, 2025  
**Status:** ✅ Complete and Ready for Testing  
**Applies To:** Kokoro engine Hindi voices (hf_alpha, hm_omega, hf_bella, hm_george)
