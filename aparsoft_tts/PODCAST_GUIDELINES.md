# Podcast Generation Guidelines for Aparsoft TTS

## 🎙️ AI Disclosure Requirements (MANDATORY)

### Platform Requirements

All AI-generated podcasts MUST include disclosure to comply with:
- **Apple Podcasts**: Requires transparent AI disclosure or face content removal
- **YouTube**: Requires disclosure for realistic synthetic content
- **Spotify**: Accepts AI podcasts but requires description disclosure

### Disclosure Format

**Required in first segment of EVERY podcast episode:**
```
"Welcome to [Podcast Name]. I'm [Host 1], and joining me is [Host 2]. 
Before we dive in, a quick note: this podcast is created using Claude by 
Anthropic for content creation and Aparsoft TTS for voice synthesis. 
We're AI-generated hosts presenting researched [topic] in a conversational 
format. Now, let's get into today's story!"
```

**Required in podcast description (for upload):**
```
This podcast is AI-generated using Claude (Anthropic) for content creation 
and Aparsoft TTS for voice synthesis. While the information is researched 
and accurate, the hosts [Host Names] are AI-generated personalities designed 
to present [topic] in an engaging conversational format.
```

### Ethical Guidelines

Based on FTC compliance and industry best practices:

1. **Transparency**: Always disclose AI use at the start of episodes
2. **Authenticity**: Make it clear hosts are AI, not real people
3. **Accuracy**: Ensure all factual content is researched and verified
4. **Trust**: Build listener trust through consistent ethical practices
5. **Credit**: Mention tools used (Claude, Aparsoft TTS) to acknowledge technology

---

## 🗣️ Creating Natural Podcast Conversations

### The Problem: Sounding Like Newsreaders

❌ **Avoid:**
- Long monologues without interaction
- Reading lists or bullet points verbatim  
- No questions or reactions between hosts
- Constant formal tone throughout
- Each host finishing complete thoughts independently

### The Solution: Natural Dialogue Patterns

✅ **Do:**
- Interrupt naturally with reactions: "Wait, really?" "That's huge!"
- Ask each other questions: "What do you think about this?" "Did you see that?"
- Use shorter, conversational sentences
- Vary tone based on content (excited, curious, skeptical)
- Show genuine reactions to information
- Build on each other's points

### Conversational Techniques

#### 1. **Question-Answer Flow**
```python
Host1: "Did you hear about the new AMD deal?"
Host2: "I did! Six gigawatts, right?"
Host1: "Exactly! What do you think this means for Nvidia?"
```

#### 2. **Reactions & Interjections**
```python
Host1: "...and AMD stock jumped 30% on the news."
Host2: "Thirty percent?! That's insane."
```

#### 3. **Build-Up & Reveal**
```python
Host1: "Okay, are you ready for this stat?"
Host2: "Hit me."
Host1: "700 million weekly users."
```

#### 4. **Agreement & Elaboration**
```python
Host2: "Would you agree with that assessment?"
Host1: "100%. And I'll add this - they're not just..."
```

#### 5. **Conversational Pauses**
Use short segments instead of long ones:
- Single sentence reactions
- Short questions
- Brief confirmations ("Right.", "Exactly.", "Makes sense.")

---

## 🎚️ Voice Speed Guidelines

Adjust speed (0.5-2.0) based on emotional context:

### Speed Recommendations

| Context | Speed | Example |
|---------|-------|---------|
| **Disclosure/Important Info** | 1.0x | Opening disclosure, key facts |
| **Casual Conversation** | 1.0-1.05x | General dialogue |
| **Excitement/Big News** | 1.1-1.2x | Revealing statistics, major announcements |
| **Explanations** | 1.0-1.05x | Technical details, complex concepts |
| **Questions** | 0.95-1.0x | Asking for opinions, seeking clarity |
| **Reactions** | 1.0-1.15x | Short responses, exclamations |

### Speed Variation Strategy

**Mix it up within episodes:**
```python
segments = [
    {"text": "Welcome...", "speed": 1.0},  # Disclosure
    {"text": "Thanks! And wow...", "speed": 1.1},  # Excitement
    {"text": "Right? Okay, so...", "speed": 1.0},  # Transition
    {"text": "It's a game changer...", "speed": 1.05},  # Explanation
    {"text": "Six gigawatts!", "speed": 1.15},  # Reveal
]
```

---

## 📝 Script Structure Best Practices

### Episode Opening (ALWAYS Include Disclosure)

```python
{
    "name": "disclosure_intro",
    "text": "[AI Disclosure Statement]",
    "speed": 1.0,
    "voice": "af_sarah"
}
```

### Body: Conversational Flow

- 15-25 segments per episode for dynamic feel
- Mix short (5-10 words) and medium (20-40 words) segments
- Questions every 3-5 segments
- Reactions scattered throughout
- Build tension with teasers ("Are you ready for this?")

### Closing

```python
{
    "name": "outro",
    "text": "Alright everyone, that's it for today's [Podcast Name]. Thanks for listening!",
    "speed": 1.0,
    "voice": "af_sarah"
}
```

---

## 👥 Multi-Voice Dynamics

### Voice Pairing Strategies

**Professional News/Tech Podcasts:**
- `am_michael` (American Male - Professional, Clear)
- `af_sarah` (American Female - Warm, Expressive)

**British Style:**
- `bm_george` (British Male)
- `bf_emma` (British Female)

**Host Personality Tips:**
- **Host A (Primary)**: Leads topics, asks questions, provides structure
- **Host B (Supporting)**: Reacts, elaborates, challenges assumptions

### Alternating Pattern

Avoid: A-A-A-A-B-B-B-B (blocks feel robotic)

Prefer: A-B-A-B-A-B-A-A-B (natural back-and-forth with occasional double turns)

---

## 🎭 Podcast-Specific Use Cases

### News & Analysis Podcasts
- Start with AI disclosure
- Mix fact presentation with analysis
- Ask "what does this mean?" frequently
- Speed: 1.0-1.15x depending on urgency

### Interview-Style (Simulated)
- One host asks, other responds
- Use pauses and "thinking" reactions: "That's a great question..."
- Speed: 0.95-1.05x for thoughtful responses

### Educational Content
- Break complex topics into Q&A
- Use "Let me explain..." transitions
- Speed: 1.0-1.05x for clarity

### Entertainment/Comedy
- Faster reactions (1.1-1.2x)
- More interjections and jokes
- Playful disagreements

---

## ⚠️ Common Mistakes to Avoid

1. **Forgetting AI Disclosure** - ALWAYS include in first segment
2. **Too Long Segments** - Keep most under 30 seconds
3. **No Questions** - Add "What do you think?" type questions
4. **Monotone Speed** - Vary 0.95x-1.2x based on emotion
5. **Reading Lists** - Convert to conversational exchanges
6. **No Reactions** - Add "Wow!", "Really?", "That's huge!"
7. **Forgetting Names** - Use podcast name in intro/outro

---

## 📊 Quality Checklist

Before generating, verify:

- [ ] AI disclosure in first segment (mandatory)
- [ ] 15+ segments for natural flow
- [ ] At least 3-5 questions between hosts
- [ ] Speed varies (1.0-1.2x range)
- [ ] Voices alternate naturally
- [ ] Short reactive segments included
- [ ] Podcast name mentioned in intro/outro
- [ ] Appropriate gap duration (0.4-0.6s)

---

## 🔗 Additional Resources

### Ethical AI Use:
- FTC AI Compliance Guidelines
- Apple Podcasts Content Guidelines
- YouTube AI Disclosure Requirements

### Podcast Best Practices:
- NPR Podcast Standards
- NotebookLM Conversational AI Study
- Professional Podcast Production Guides

---

**Last Updated**: October 2025  
**Version**: 2.0  
**Maintained By**: Aparsoft AI Insights Team
