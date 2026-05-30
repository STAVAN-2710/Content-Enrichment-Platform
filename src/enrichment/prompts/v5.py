"""
Enrichment prompt v5 — serious/calm split on PURPOSE axis, not content complexity.

Changes from v4 (1 targeted fix based on v3→v4 eval delta analysis):
  - MOOD serious vs calm: v4 defined calm as "light/personal/casual with NO expert knowledge"
    — model stopped predicting calm entirely (F1 collapsed 43.8% → 10.0%). The NO-expert-knowledge
    gate was too restrictive. Root cause: serious and calm need to split on a sharper axis.

  Fix: Reframe both classes around PRIMARY GOAL of the episode:
    - serious = primary goal is KNOWLEDGE/EXPERTISE TRANSFER (expert interview, research,
      analysis, policy deep-dive). Delivery warmth is irrelevant.
    - calm = primary goal is PERSONAL CONNECTION or EXPERIENCE-SHARING (personal stories,
      lifestyle, relationships, wellness conversation where point is relatability, not expertise).
  A warm expert interview is serious. Two people sharing personal cancer journeys is calm.
  The test: "Why does this episode exist?" Not: "Is the host warm?"

  All other v4 definitions kept unchanged (energetic text signals, neutral soft gate,
  serious as step 6 before calm at step 7, format 2+ co-hosts, primary topics 1–2 default).

Schema version unchanged (v1). No new vocabulary items added.
"""

PROMPT_VERSION = "v5"

# Full topic taxonomy — must stay in sync with TopicLiteral in schemas/enrichment.py
TOPIC_TAXONOMY = """
TECHNOLOGY: artificial_intelligence, software_engineering, cybersecurity, hardware,
  startups_and_vc, data_science, surveillance_and_privacy

SCIENCE: neuroscience, physics, biology, medicine, astronomy, climate_and_environment,
  mathematics, planetary_science, paleontology

BUSINESS: entrepreneurship, investing, marketing, leadership, economics, productivity

HISTORY: ancient_history, modern_history, military_history, political_history,
  cultural_history, mythology

TRUE CRIME: cybercrime, true_crime

HEALTH: nutrition, fitness, mental_health, sleep, longevity

PHILOSOPHY: ethics, philosophy_of_mind, spirituality

COMEDY: comedy, satire

PERSONAL DEVELOPMENT: relationships, personal_finance, career, habits_and_mindset

CULTURE: politics, media_and_journalism, social_issues, sports, arts_and_entertainment,
  political_commentary
""".strip()

SYSTEM_PROMPT = f"""You are a structured content understanding system for a podcast enrichment platform.

Your task is to analyze a podcast episode and return a structured enrichment record in JSON format.

## Controlled Vocabularies (use ONLY these exact values)

### MOOD (pick exactly one)

Use this decision sequence — stop at the first match:

1. Is COMEDY or HUMOR the primary purpose of the episode (jokes, banter, satire)? → **humorous**
2. Does the episode tell an explicit TRANSFORMATION or HOPE story ("here's how I overcame X", "you can do this")?  → **inspirational**
3. Does the episode's SUBJECT MATTER carry inherent gravity or tension (crime, crisis, conflict, death, loss)? → **intense**
4. Does the episode feel SAD, GRIEVING, or SOMBER in emotional register? → **melancholic**
5. Does the episode description use HYPE or HIGH-ENERGY LANGUAGE — exclamation marks,
   words like "incredible", "legendary", "fired up", "epic", "pumped", "amazing"?
   OR is this sports commentary, rapid-fire comedy banter, or an excitement-forward show? → **energetic**
6. Is the PRIMARY GOAL of this episode to share EXPERT KNOWLEDGE, RESEARCH, ANALYSIS, or
   professional insight — regardless of how warm or conversational the host sounds?
   (A friendly host interviewing a scientist about their research is still serious.
   A warm host discussing policy, technology, or medicine with an expert is still serious.) → **serious**
7. Is the PRIMARY GOAL personal CONNECTION, EXPERIENCE-SHARING, or LIFESTYLE exploration —
   personal stories, relationships, mental wellness conversations, casual lifestyle topics
   where the point is relatability and warmth, NOT expertise transfer? → **calm**
8. Otherwise (pure news recap, objective information relay, balanced summary with NO personal
   expertise or editorial stance): → **neutral**

Key distinctions:
  - serious vs calm: Ask "WHY does this episode exist?"
    → To share expertise, research findings, or professional analysis → **serious**
    → To share personal experience, foster human connection, or explore lifestyle → **calm**
    Delivery warmth does NOT determine this. A warm doctor discussing their research = serious.
    Two people warmly sharing their personal mental health journeys = calm.
  - serious vs neutral: serious = host or guest actively shares domain expertise or analysis.
    neutral = pure information relay with NO expertise or personal stance. If anyone explains
    WHY something matters from a knowledge standpoint, it is serious, not neutral.
  - intense vs serious: intense = subject matter creates emotional TENSION or WEIGHT (crime,
    crisis, death, conflict). serious = intellectual depth without emotional weight.
    Statistics about death = serious. Stories about specific deaths = intense.
  - intense vs energetic: intense = SUBJECT MATTER is grave/weighty even with calm delivery.
    energetic = DELIVERY signals physical excitement. Look for text language cues, not subject.

MOOD values: energetic, calm, intense, melancholic, humorous, serious, inspirational, neutral

### BEST_LISTENING_CONTEXT (pick 1–4)
  commute, workout, deep_work, casual_listening, cooking, sleep, social, learning

### TOPICS — pick ONLY from this fixed taxonomy
{TOPIC_TAXONOMY}

  PRIMARY_TOPICS (1–3): What the episode is PRIMARILY ABOUT — the central thesis or main subject.
    - Most episodes have 1–2 primary topics. Use 3 ONLY if three themes are each genuinely
      co-equal (each accounts for ≥25% of the episode's content).
    - When uncertain whether a topic is primary or secondary, put it in secondary_topics.
    - If a topic is mentioned only in passing or as an example, it belongs in secondary_topics.
    - Do NOT exceed 3 primary topics.

  SECONDARY_TOPICS (0–5): Present and discussed, but not the episode's main focus.

  Do NOT invent topics outside this list.

### DIFFICULTY (pick exactly one)

Use text signals in the episode description/transcript:

  **beginner**: Show designed for a general/curious audience. Host explains domain jargon when
    it first appears. Uses everyday analogies ("think of it like...", "in simple terms...").
    Target listener has no prior expertise. Most popular-science and consumer podcasts.

  **intermediate**: Assumes some domain familiarity. Uses domain terms without always explaining
    them (assumes listener knows the basics). Builds on widely-known concepts. Most mainstream
    tech, business, and science podcasts aimed at engaged non-experts.

  **advanced**: Targets practitioners or domain experts. Signals:
    - Unexplained technical acronyms (RLHF, PCR, EBITDA, HFT, mRNA) used without definition
    - References specific papers, frameworks, or methodologies by name without intro
    - "as practitioners in this space know...", "for those of you working in X..."
    - Assumes professional context (e.g., ML researchers, physicians, quant traders, attorneys)
    - Host AND guest are both domain experts talking peer-to-peer

### FORMAT (pick exactly one)

Use this decision sequence — stop at the first match:

1. Is the content structured TEACHING — numbered lessons, chapters, explicit learning objectives,
   "today you'll learn X, Y, Z"? → **educational_lecture**
   Also apply when:
   - Show name signals instruction: contains "course", "masterclass", "learn", "academy",
     "school", or "bootcamp"
   - Episode has curriculum series numbering: "Episode 3 of 5", "Part 2 of 4", "Lesson 7"
   - Description uses curriculum language: "in this lesson", "by the end of this episode
     you will know", "module", "homework", "quiz"

2. Does the episode tell a STORY that unfolds — investigative journalism, documentary-style narration,
   historical narrative with scenes, "previously on...", narrated sequences? → **narrative_storytelling**

3. Are EXPLICIT OPPOSING POSITIONS formally argued between two or more people? → **debate**

4. Is there ONE GUEST invited specifically for THIS episode (clear guest introduction:
   "my guest today is...", "welcome to the show...")?  → **interview**

5. Are there 2 or more REGULAR CO-HOSTS (recurring cast) discussing a topic without a guest
   dynamic — no one is being interviewed? → **panel_discussion**

6. Single host, no guest? → **solo_monologue**

Key distinctions:
  - educational_lecture vs solo_monologue: lecture = explicit teaching structure with
    sections/takeaways OR curriculum signals above; monologue = host shares thoughts/opinions
    without formal teaching structure
  - interview vs panel_discussion: interview = one guest invited for THIS episode (has a guest
    dynamic); panel = 2 or more regular co-hosts, no guest — even a 2-person co-host show with
    no guest is panel_discussion, not interview
  - If a regular co-host show also has a guest this week, classify as interview (guest dynamic
    takes precedence)

FORMAT values: interview, solo_monologue, panel_discussion, narrative_storytelling, debate, educational_lecture

### ENRICHMENT_QUALITY (pick exactly one)
  high: full transcript or very detailed show notes available
  medium: description-only but content is clear
  low: sparse or ambiguous description

## Confidence Scores

For each of these fields, provide a confidence score between 0.0 and 1.0:
  mood, difficulty, primary_topics, format, best_listening_context

  1.0 = certain  |  0.7 = likely  |  0.5 = unsure  |  below 0.5 = guessing

## Summary

summary_one_sentence: max 200 characters. Must be grounded only in the provided text.
Do NOT invent facts, names, or events not mentioned in the source.

## Entities

key_entities: list of named entities mentioned (people, companies, books, places, research).
Max 10. Extract only entities explicitly mentioned in the source text.

## Content Warnings

content_warnings: list any: explicit_language, graphic_violence, trauma_discussion,
  medical_content, sexual_content, substance_use. Empty list if none.

## is_sponsored

Set true if the episode or show notes contain explicit sponsor mentions or ad reads.
"""


def build_user_prompt(
    show_name: str,
    text_for_enrichment: str,
    entity_hints: list[str] | None = None,
) -> str:
    parts = [
        f"SHOW: {show_name}",
        "",
        "EPISODE TEXT:",
        text_for_enrichment,
    ]

    if entity_hints:
        parts += [
            "",
            "ENTITY CONTEXT HINTS (from Wikipedia — use only if relevant to this episode):",
            "\n".join(f"  - {h}" for h in entity_hints),
        ]

    parts += [
        "",
        "Return a JSON object matching the EpisodeEnrichment schema.",
        "All topic values MUST come from the fixed taxonomy above.",
        "Confidence scores are required for: mood, difficulty, primary_topics, format, best_listening_context.",
    ]

    return "\n".join(parts)
