# aparsoft_tts/mcp_server/mcp_prompts.py

"""MCP Prompts implementation for Aparsoft TTS.

Implements 4 guided workflow prompts using FastMCP's @mcp.prompt decorator:
  - podcast_creator: Step-by-step podcast creation guide with MANDATORY AI disclosure
  - voice_selector: Interactive voice selection based on content requirements
  - script_optimizer: Best practices for TTS-optimized script writing
  - troubleshoot_tts: Diagnostic guide for common quality issues

Prompts provide reusable templates and workflows to guide users through complex tasks.
Each prompt uses Pydantic models for parameter validation and generates contextual
guidance based on user requirements.

Utility functions are imported from mcp_utils.py for template generation.
"""

import warnings
from pydantic import BaseModel, Field, field_validator

from aparsoft_tts.mcp_server import mcp_utils
from aparsoft_tts.mcp_server.mcp_server_main import mcp

# Suppress all warnings to prevent non-JSON output in MCP
warnings.filterwarnings("ignore")

from aparsoft_tts.utils.logging import bind_context, get_logger

log = get_logger(__name__)


# ==============================================================================
# MCP PROMPTS - Guided workflows and best practice templates
# ==============================================================================
# Prompts guide users through complex workflows like podcast creation and
# voice selection, enforcing best practices (e.g., mandatory AI disclosure).


class PodcastPromptArgs(BaseModel):
    """Arguments for podcast creation prompt."""

    topic: str = Field(description="Podcast topic or theme")
    duration_minutes: int = Field(default=10, description="Target duration in minutes", ge=1, le=60)
    num_hosts: int = Field(default=2, description="Number of hosts/speakers", ge=1, le=4)
    style: str = Field(default="conversational", description="Podcast style")

    @field_validator("style")
    @classmethod
    def validate_style(cls, v: str) -> str:
        """Validate podcast style."""
        valid_styles = ["conversational", "interview", "educational", "news", "storytelling"]
        if v.lower() not in valid_styles:
            raise ValueError(f"Style must be one of: {', '.join(valid_styles)}")
        return v.lower()


@mcp.prompt()
async def podcast_creator(args: PodcastPromptArgs) -> str:
    """Guide for creating professional AI-generated podcasts.

    Provides comprehensive step-by-step guidance including:
    1. MANDATORY AI disclosure (legal/ethical requirement)
    2. Content structure and segmentation
    3. Voice and speed selection
    4. Natural dialogue writing tips
    5. Technical settings optimization

    ⚠️ CRITICAL: First segment MUST include AI disclosure per:
    - Apple Podcasts guidelines
    - YouTube ToS for AI content
    - Spotify recommendations

    Args:
        args: Podcast parameters (topic, duration, hosts, style)

    Returns:
        Comprehensive podcast creation guide with examples

    Example:
        >>> await podcast_creator(PodcastPromptArgs(
        ...     topic="Artificial Intelligence Ethics",
        ...     duration_minutes=15,
        ...     num_hosts=2,
        ...     style="conversational"
        ... ))
    """
    try:
        bind_context(
            operation="podcast_creator_prompt",
            topic=args.topic,
            duration=args.duration_minutes,
            style=args.style,
        )

        guide = mcp_utils.create_podcast_prompt(
            topic=args.topic,
            duration_minutes=args.duration_minutes,
            num_hosts=args.num_hosts,
            style=args.style,
        )

        log.info(
            "mcp_prompt_podcast_creator_generated",
            topic=args.topic,
            duration=args.duration_minutes,
            num_hosts=args.num_hosts,
            style=args.style,
        )

        return guide

    except Exception as e:
        log.error("mcp_prompt_podcast_creator_error", error=str(e))
        return f"❌ Error generating podcast guide: {str(e)}"


class VoiceSelectionPromptArgs(BaseModel):
    """Arguments for voice selection prompt."""

    content_type: str = Field(description="Type of content to create")
    tone: str = Field(default="professional", description="Desired tone")
    audience: str = Field(default="adults", description="Target audience")
    duration: str = Field(default="medium", description="Content duration")

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v: str) -> str:
        """Validate tone."""
        valid_tones = ["professional", "casual", "warm", "authoritative", "energetic", "calm"]
        if v.lower() not in valid_tones:
            raise ValueError(f"Tone must be one of: {', '.join(valid_tones)}")
        return v.lower()

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: str) -> str:
        """Validate duration."""
        valid_durations = ["short", "medium", "long"]
        if v.lower() not in valid_durations:
            raise ValueError(f"Duration must be one of: {', '.join(valid_durations)}")
        return v.lower()


@mcp.prompt()
async def voice_selector(args: VoiceSelectionPromptArgs) -> str:
    """Interactive guide for selecting the optimal voice for your content.

    Analyzes your requirements and recommends voices based on:
    - Content type (tutorial, podcast, audiobook, etc.)
    - Desired tone (professional, warm, casual, etc.)
    - Target audience
    - Content duration (affects quality tier recommendation)

    Provides:
    - Top 3 voice recommendations with rationale
    - Quality tier explanations (Premium/Professional/Good)
    - Speed recommendations for content type
    - Decision tree for quick selection

    Args:
        args: Content requirements (type, tone, audience, duration)

    Returns:
        Personalized voice selection guide

    Example:
        >>> await voice_selector(VoiceSelectionPromptArgs(
        ...     content_type="tutorial",
        ...     tone="professional",
        ...     audience="developers",
        ...     duration="medium"
        ... ))
    """
    try:
        bind_context(
            operation="voice_selector_prompt",
            content_type=args.content_type,
            tone=args.tone,
            duration=args.duration,
        )

        guide = mcp_utils.create_voice_selection_prompt(
            content_type=args.content_type,
            tone=args.tone,
            audience=args.audience,
            duration=args.duration,
        )

        log.info(
            "mcp_prompt_voice_selector_generated",
            content_type=args.content_type,
            tone=args.tone,
            audience=args.audience,
            duration=args.duration,
        )

        return guide

    except Exception as e:
        log.error("mcp_prompt_voice_selector_error", error=str(e))
        return f"❌ Error generating voice selection guide: {str(e)}"


class ScriptOptimizationPromptArgs(BaseModel):
    """Arguments for script optimization prompt."""

    target_audience: str = Field(default="general", description="Target audience for optimization")


@mcp.prompt()
async def script_optimizer(args: ScriptOptimizationPromptArgs) -> str:
    """Guide for optimizing scripts for natural-sounding TTS output.

    Provides comprehensive optimization techniques:
    - Sentence length and structure
    - Punctuation for natural pacing
    - Pronunciation handling (acronyms, numbers, technical terms)
    - Paragraph structuring for optimal token counts
    - Conversational style guidelines
    - Common TTS pitfalls to avoid

    Includes before/after examples and a complete optimization workflow.

    Args:
        args: Optimization parameters (target audience)

    Returns:
        Complete script optimization guide

    Example:
        >>> await script_optimizer(ScriptOptimizationPromptArgs(
        ...     target_audience="technical professionals"
        ... ))
    """
    try:
        bind_context(operation="script_optimizer_prompt", target_audience=args.target_audience)

        guide = mcp_utils.create_script_optimization_prompt(target_audience=args.target_audience)

        log.info("mcp_prompt_script_optimizer_generated", target_audience=args.target_audience)

        return guide

    except Exception as e:
        log.error("mcp_prompt_script_optimizer_error", error=str(e))
        return f"❌ Error generating script optimization guide: {str(e)}"


class HindiScriptOptimizationPromptArgs(BaseModel):
    """Arguments for Hindi script optimization prompt."""

    tts_engine: str = Field(default="kokoro", description="TTS engine being used")


@mcp.prompt()
async def hindi_script_optimizer(args: HindiScriptOptimizationPromptArgs) -> str:
    """Guide for optimizing Hindi scripts for natural TTS output with punctuation best practices.

    Provides comprehensive optimization techniques for Hindi text:
    - Sentence length and structure for Hindi
    - Punctuation rules: When to use . (full stop) vs । (danda)
    - 🔴 CRITICAL: Kokoro engine requires English full stops (.)
    - Pronunciation handling (Hindi-specific terms, numbers)
    - Paragraph structuring for optimal rendering
    - Conversational Hindi style guidelines
    - Common Hindi TTS pitfalls to avoid

    ⚠️  ENGINE-SPECIFIC PUNCTUATION RULES:
    - Kokoro engine (Hindi voices): Use . (English full stop)
    - Indic engine: Can use both . and । (Hindi danda)
    - Reason: Kokoro's Hindi model trained on English punctuation

    Args:
        args: Engine and optimization parameters

    Returns:
        Complete Hindi script optimization guide

    Example:
        >>> await hindi_script_optimizer(HindiScriptOptimizationPromptArgs(
        ...     tts_engine="kokoro"
        ... ))
    """
    try:
        bind_context(operation="hindi_script_optimizer_prompt", tts_engine=args.tts_engine)

        guide = f"""🇮🇳 **HINDI SCRIPT OPTIMIZATION GUIDE FOR TTS**

**Current Engine:** {args.tts_engine}

---

## 🎯 THE GOLDEN RULE FOR KOKORO HINDI

**For BEST QUALITY with Kokoro Hindi voices, follow these TWO critical rules:**

1. **📝 Write English words PHONETICALLY in Devanagari script**
   - MATHEMATICS → मैथमेटिक्स
   - SCIENCE → साइंस
   - TECHNOLOGY → टेक्नोलॉजी
   - IMPORTANT → इम्पॉर्टेंट

2. **🔤 Use English full stops (.) NOT Hindi danda (।)**
   - "बच्चों, आज हम मैथमेटिक्स सीखेंगे. यह इम्पॉर्टेंट है." ✅
   - "बच्चों, आज हम MATHEMATICS सीखेंगे।" ❌

**Why?** Kokoro's Hindi model was trained on phonetic Devanagari text with English punctuation patterns.

---

## 🔴 CRITICAL: BEST PRACTICES FOR KOKORO HINDI VOICES

### Kokoro Engine (Hindi Voices: hf_alpha, hm_omega, etc.)

**REQUIREMENTS FOR BEST QUALITY:**

1. **Use Phonetic Hindi Devanagari for English words**
2. **Use English Full Stop (.) not Hindi Danda (।)**

```
✅ CORRECT for Kokoro (Phonetic Devanagari + English full stop):
"बच्चों, आज हम मैथमेटिक्स सीखेंगे. टेक्नोलॉजी बहुत इम्पॉर्टेंट है."

❌ WRONG for Kokoro (Raw English words):
"बच्चों, आज हम MATHEMATICS सीखेंगे। TECHNOLOGY बहुत महत्वपूर्ण है।"

❌ WRONG for Kokoro (Hindi Danda):
"बच्चों, आज हम गणित सीखेंगे। यह महत्वपूर्ण है।"
```

**Why?** 
- Kokoro's Hindi model trained on **phonetic Devanagari** (English words written in Hindi script)
- English punctuation (.) provides better rhythm and natural pacing
- Example conversions: MATHEMATICS → मैथमेटिक्स, SCIENCE → साइंस, TECHNOLOGY → टेक्नोलॉजी

---

### Indic Engine (Hindi: divya, madhav, rohit, etc.)

**FLEXIBILITY: Can use both . and ।**

```
✅ Both are acceptable for Indic:
"बच्चों, आज हम गणित सीखेंगे. द़ऐम डो और तब त॒के सुनॉ."

✅ Also acceptable:
"बच्चों, आज हम गणित सीखेंगे। द़ईम डो और तब त॒के सुन३।"
```

**Why?** Indic engine natively supports traditional Hindi punctuation.

---

## 📄 SENTENCE STRUCTURE OPTIMIZATION

### Keep Sentences Short with Phonetic Devanagari

```
❌ Too Long with English words (hard to pronounce naturally):
"बच्चों, आज की CLASS में हम ADVANCED MATHEMATICS के TOPICS सीखेंगे।"

✅ Better (short, phonetic Devanagari, English punctuation):
"बच्चों, आज की क्लास शुरू करते हैं. हम एडवांस्ड मैथमेटिक्स सीखेंगे. टॉपिक्स बहुत इंटरेस्टिंग हैं."
```

**Key Rules:**
- Convert English words to phonetic Devanagari: CLASS → क्लास, ADVANCED → एडवांस्ड
- Use English full stop (.) between sentences
- Keep sentences 5-15 words for natural flow

---

## 🔢 NUMBER AND TECHNICAL TERM HANDLING

### Write Numbers Phonetically

```
✅ Good:
"1000 और 2000 के वच की तुलना करें."

❌ Poor (unclear pronunciation):
"हज़ार और दो हज़ार के वर्ष"

Better:
"1000 साल और 2000 साल की तुलना."
```

### Common Abbreviations

```
✅ Write abbreviations phonetically in Devanagari:
"USA" → "यू एस ए" or "अमेरिका"
"BMW" → "बी एम डब्ल्यू"
"AI" → "आर्टिफिशियल इंटेलिजेंस"
"MATHEMATICS" → "मैथमेटिक्स"
```

💡 **KEY PRINCIPLE:** All English words should be written phonetically in Devanagari script for best Kokoro results.

---

## 🁲 CONVERSATIONAL HINDI STYLE

### Use Natural Dialogue Markers

```
✅ Add personality with phonetic English words:
"तो सुनो. बहुत इम्पॉर्टेंट है. समझते हो? हां!"

❌ Robotic or with raw English:
"इसको सुनें और UNDERSTAND करें."
```

💡 **TIP:** Convert words like IMPORTANT → इम्पॉर्टेंट, UNDERSTAND → अंडरस्टैंड

---

## ❌ COMMON MISTAKES TO AVOID

### Mistake #1: Using Raw English Words Instead of Phonetic Devanagari
```
❌ WRONG for Kokoro:
"बच्चों, आज हम MATHEMATICS सीखेंगे. SCIENCE भी IMPORTANT है।"
(Raw English words + wrong punctuation)

✅ CORRECT:
"बच्चों, आज हम मैथमेटिक्स सीखेंगे. साइंस भी इम्पॉर्टेंट है."
(Phonetic Devanagari + English full stop)
```

### Mistake #2: Mixing Punctuation
```
❌ WRONG for Kokoro:
"बच्चों, आज हम मैथमेटिक्स सीखेंगे. आगे की प्रॉब्लम्स सीखेंगे।"
(Mix of . and ।)

✅ CORRECT:
"बच्चों, आज हम मैथमेटिक्स सीखेंगे. आगे की प्रॉब्लम्स सीखेंगे."
(Consistent use of . only)
```

### Mistake #3: Too Many Words Between Pauses
```
❌ HARD TO READ:
"बच्चों आज की क्लास में हम एडवांस्ड मैथमेटिक्स के टॉपिक्स और कॉन्सेप्ट्स को डिटेल में सीखेंगे।"

✅ BETTER:
"बच्चों, आज की क्लास शुरू करें. हम एडवांस्ड मैथमेटिक्स सीखेंगे. टॉपिक्स बहुत इंटरेस्टिंग हैं."
```

---

## 📗 QUICK CHECKLIST BEFORE PROCESSING

- [ ] All English words converted to phonetic Devanagari (MATHEMATICS → मैथमेटिक्स)
- [ ] All sentences use . (not ।) if using Kokoro
- [ ] Sentences are 5-15 words each
- [ ] Numbers are written as digits (1000, 2000)
- [ ] Abbreviations written phonetically (USA → यू एस ए)
- [ ] No repeated punctuation (.. or ।।)
- [ ] No mixing of . and । in Kokoro
- [ ] No raw English words like "MATHEMATICS" or "SCIENCE"
- [ ] Text reads naturally when spoken aloud

---

## 🎩 BEFORE/AFTER EXAMPLES

### Example 1: Educational Content with Technical Terms

```
❌ ORIGINAL (Raw English + Wrong Punctuation):
"बच्चों, आज हम MATHEMATICS सीखेंगे। ALGEBRA और GEOMETRY बहुत IMPORTANT हैं।"

✅ OPTIMIZED (Phonetic Devanagari + English Punctuation):
"बच्चों, आज हम मैथमेटिक्स सीखेंगे. अल्जेब्रा और जियोमेट्री बहुत इम्पॉर्टेंट हैं."
```

### Example 2: Technology Tutorial

```
❌ ORIGINAL (Mixed Format):
"आज हम PROGRAMMING सीखेंगे। PYTHON एक POWERFUL LANGUAGE है।"

✅ OPTIMIZED (Clean Phonetic):
"आज हम प्रोग्रामिंग सीखेंगे. पायथन एक पावरफुल लैंग्वेज है."
```

---

## 🚀 READY TO CREATE AMAZING HINDI TTS?

1. ✅ Check your engine (Kokoro = . only)
2. ✅ Optimize sentences (short and natural)
3. ✅ Test on a small sample first
4. ✅ Adjust based on output
5. ✅ Iterate and improve!

Happy creating! 🇮🇳
"""

        log.info("mcp_prompt_hindi_script_optimizer_generated", tts_engine=args.tts_engine)

        return guide

    except Exception as e:
        log.error("mcp_prompt_hindi_script_optimizer_error", error=str(e))
        return f"❌ Error generating Hindi script optimization guide: {str(e)}"


@mcp.prompt()
async def troubleshoot_tts() -> str:
    """Comprehensive troubleshooting guide for TTS quality issues.

    Covers common problems and solutions:
    - Robotic/unnatural voice
    - Mispronunciations
    - Pacing issues (too fast/slow)
    - Audio artifacts (clicks, pops)
    - Volume inconsistencies
    - Awkward pauses
    - Script length issues
    - Voice mismatches

    Includes diagnostic workflow and prevention checklist.

    Returns:
        Complete TTS troubleshooting guide

    Example:
        >>> await troubleshoot_tts()
    """
    try:
        bind_context(operation="troubleshoot_tts_prompt")

        guide = mcp_utils.create_troubleshooting_prompt()

        log.info("mcp_prompt_troubleshoot_tts_generated")

        return guide

    except Exception as e:
        log.error("mcp_prompt_troubleshoot_tts_error", error=str(e))
        return f"❌ Error generating troubleshooting guide: {str(e)}"


class EducationalScriptPromptArgs(BaseModel):
    """Arguments for educational script processing prompt."""

    script_type: str = Field(default="youtube_tutorial", description="Type of educational content")
    has_segments: bool = Field(default=True, description="Whether script has multiple segments")
    has_variable_speeds: bool = Field(
        default=True, description="Whether script uses variable speeds"
    )


@mcp.prompt()
async def educational_script_processor(args: EducationalScriptPromptArgs) -> str:
    """Guide for processing educational video scripts correctly.

    **🎓 CRITICAL: Educational scripts need special handling!**

    This prompt explains:
    - When to use which TTS tool for educational content
    - How to parse educational script markdown
    - Common mistakes and how to avoid them
    - Tool selection decision tree

    **Common Mistake:**
    ❌ Using `process_script` on markdown educational scripts
    → Results in voice reading "hash hash hash" and all metadata!

    ✅ Use `process_educational_script` instead for:
    - Scripts with ## SEGMENT markers
    - Variable speed annotations [Speed: 1.2x]
    - Markdown formatting to ignore

    Args:
        args: Script characteristics

    Returns:
        Complete guide for processing educational scripts

    Example:
        >>> await educational_script_processor(EducationalScriptPromptArgs(
        ...     script_type="youtube_tutorial",
        ...     has_segments=True,
        ...     has_variable_speeds=True
        ... ))
    """
    try:
        bind_context(
            operation="educational_script_processor_prompt",
            script_type=args.script_type,
            has_segments=args.has_segments,
        )

        guide = (
            f"""🎓 **EDUCATIONAL SCRIPT PROCESSING GUIDE**

**Script Type:** {args.script_type}
**Has Segments:** {args.has_segments}
**Variable Speeds:** {args.has_variable_speeds}

---

### ⚠️ CRITICAL: TOOL SELECTION DECISION TREE

**BEFORE YOU START - Ask yourself:**

**Q1: Is this a markdown file with ## SEGMENT headers?**
→ **YES**: Continue to Q2
→ **NO**: Go to Q4

**Q2: Does it have variable speeds like [Speed: 1.2x]?**
→ **YES**: Use `process_educational_script` ✅
→ **NO**: Continue to Q3

**Q3: Does it have multiple segments that need different voices/speeds?**
→ **YES**: Manually extract segments → Use `generate_podcast` ✅
→ **NO**: Extract just narration text → Use `process_script` ⚠️

**Q4: Is it plain text without any markdown?**
→ **YES**: Use `process_script` ✅
→ **NO**: Extract text first, then use appropriate tool

---

### 🚨 COMMON MISTAKES TO AVOID

**MISTAKE #1: Using process_script on markdown files**
```
❌ WRONG:
await process_script(ProcessScriptRequest(
    script_path="tutorial.md"  # Has ## SEGMENT headers!
))

Result: Voice reads "hash hash hash SEGMENT 1 dash Introduction
        bracket Speed colon 1.2x bracket..."
```

```
✅ CORRECT:
await process_educational_script(ProcessEducationalScriptRequest(
    script_path="tutorial.md",
    voice="hf_beta"
))

Result: Clean narration with proper speeds per segment!
```

**MISTAKE #2: Not recognizing segment patterns**

If you see THIS in the script:
```markdown
## SEGMENT 1 - Introduction [Speed: 1.2x]
Narration text here...

## SEGMENT 2 - Main Content [Speed: 1.1x]
More narration...
```

→ This is an **EDUCATIONAL SCRIPT** with segments!
→ Use `process_educational_script` tool!

**MISTAKE #3: Passing raw markdown to generate_podcast**

❌ Don't pass markdown headers/metadata as "text"
✅ Extract ONLY the actual narration text

---

### ✅ CORRECT WORKFLOW FOR YOUR SCRIPT

**Your script characteristics:**
- Type: {args.script_type}
- Has segments: {args.has_segments}
- Variable speeds: {args.has_variable_speeds}

"""
            + (
                f"""**RECOMMENDED TOOL: `process_educational_script`** ✅

**Why:** Your script has segments with variable speeds in markdown format.

**Usage:**
```python
await process_educational_script(ProcessEducationalScriptRequest(
    script_path="your_script.md",
    voice="hf_beta",  # or hf_alpha, hm_omega, etc.
    output_path="output.wav",
    gap_duration=0.5
))
```

**What it does automatically:**
1. ✅ Parses ## SEGMENT headers
2. ✅ Extracts [Speed: X.Xx] values
3. ✅ Removes all markdown formatting
4. ✅ Ignores metadata and comments
5. ✅ Creates segments with correct speeds
6. ✅ Merges into single audio file

**You don't need to:**
- ❌ Manually extract text from each segment
- ❌ Parse speed values yourself
- ❌ Clean up markdown formatting
- ❌ Call generate_podcast manually

"""
                if args.has_segments and args.has_variable_speeds
                else f"""**RECOMMENDED APPROACH:**

1. **Extract narration text** from each segment (ignore headers/metadata)
2. **Use `generate_podcast` tool** with segments array
3. **Set speeds manually** based on content type

**Example:**
```python
await generate_podcast(GeneratePodcastRequest(
    segments=[
        PodcastSegment(
            text="Introduction narration...",
            voice="hf_beta",
            speed=1.2,
            name="intro"
        ),
        PodcastSegment(
            text="Main content narration...",
            voice="hf_beta",
            speed=1.1,
            name="main"
        )
    ],
    output_path="output.wav"
))
```
"""
            )
            + f"""

---

### 📋 QUICK REFERENCE TABLE

| Script Format | Has Segments | Variable Speeds | Tool to Use |
|---------------|--------------|-----------------|-------------|
| Markdown with ## SEGMENT | ✅ | ✅ | `process_educational_script` |
| Markdown with ## SEGMENT | ✅ | ❌ | Extract text → `generate_podcast` |
| Plain text file | ❌ | ❌ | `process_script` |
| Multiple texts | N/A | N/A | `batch_generate` |
| Single text | ❌ | ❌ | `generate_speech` |

---

### 🎯 KEY TAKEAWAYS

1. **Educational scripts** (markdown with segments) need **special handling**
2. **process_script** reads files **as-is** (includes all formatting)
3. **process_educational_script** **parses** markdown and extracts clean text
4. When in doubt: **Check for ## SEGMENT headers** → Use educational tool
5. **Variable speeds** make content more engaging → Always use when specified

---

### 💡 PRO TIP

Before processing ANY script file:
1. 🔍 Quick scan for ## SEGMENT markers
2. 👀 Look for [Speed: X.Xx] annotations
3. ✅ Choose appropriate tool based on findings
4. 🚀 Process with confidence!

---

Ready to process your educational script correctly? Let's do this! 🎓
"""
        )

        log.info("mcp_prompt_educational_script_processor_generated", script_type=args.script_type)

        return guide

    except Exception as e:
        log.error("mcp_prompt_educational_script_processor_error", error=str(e))
        return f"❌ Error generating educational script guide: {str(e)}"
