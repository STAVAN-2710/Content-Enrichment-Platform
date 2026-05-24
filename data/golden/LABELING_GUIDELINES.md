# Podcast Episode Labeling Guidelines

## Why this document exists

You will label approximately 150 podcast episodes. This reference defines every field precisely so your labels stay consistent across 20+ hours of work. Consistency matters more than perfection — a borderline call made the same way every time is more valuable than a case-by-case judgment that shifts day to day.

**When uncertain:** Default to the rule that best fits the majority of the episode, not the most memorable moment. If you genuinely cannot decide between two values and the description is too sparse to resolve it, pick the best fit and set `labeler_confidence: low`. Do not skip fields.

**Source of truth:** Label only what is present in the episode description (and title). Do not infer content from the podcast's general reputation or what you expect the show to cover.

---

## Fields

---

### `mood`

**Definition:** The conversational tone and host energy of the episode. This is about *how* the episode feels to listen to, not *what* it covers. A true crime episode can be calm; a cooking episode can be intense.

**Pick exactly one.**

| Value | What it means |
|---|---|
| `energetic` | Fast-paced, enthusiastic, high-energy delivery. Host/guest seems excited. |
| `calm` | Measured, unhurried, relaxed tone. Conversational and low-key. |
| `intense` | Focused, serious, high-stakes feeling. Could be urgent, confrontational, deeply analytical, or emotionally heavy. |
| `melancholic` | Reflective, sad, mournful, or wistful. Topics of loss, regret, or longing dominate the tone. |
| `humorous` | Jokes, banter, comedic framing are central to the episode's delivery. Laughs are the point. |
| `serious` | Sober, formal, or weighty — but not emotionally heavy in the way `intense` is. Think: measured policy discussion, careful academic explanation. |
| `neutral` | No strong tonal signature. Could go either way. Use as a last resort. |
| `inspirational` | Motivational, uplifting, forward-looking. Guest shares a transformative journey or the host delivers an encouraging message. |

#### The hardest distinction: `energetic` vs `intense`

This is the most common labeling error. Use this rule:

- **Energetic = enthusiasm driving the energy.** The host is excited, animated, maybe hyperbolic. You'd feel pumped up listening. Think: startup founder raving about a product launch, a sports commentator calling a highlight reel.
- **Intense = stakes or depth driving the energy.** The conversation feels urgent, charged, or demanding of full attention. Could be a whistleblower interview, a heated debate, or a deeply analytical breakdown. You'd feel locked in, not pumped up.

A guest can be energetic while discussing an intense topic. Judge the delivery, not the subject matter.

**Examples:**

| Description signal | Label | Reasoning |
|---|---|---|
| "We're FIRED UP about the latest AI announcements — this week's episode is a wild ride through..." | `energetic` | Enthusiasm, exclamation, "wild ride" signals high energy and excitement. |
| "Former CIA officer discusses the details of a covert operation that nearly failed..." | `intense` | High stakes, serious subject, focused and charged — not enthusiastic. |
| "Two comedians break down the week in tech news" | `humorous` | Comedic framing is explicitly the delivery mechanism. |
| "A quiet conversation about what it means to lose a parent" | `melancholic` | Loss and grief are the explicit subject; "quiet" confirms tone. |
| "Lex sits down with a researcher to walk through the math behind transformer models" | `serious` | Careful, formal, weighty — but not emotionally charged or exclamation-driven. |
| "From homeless to $50M founder — this one will leave you changed" | `inspirational` | Transformative journey, motivational framing. |
| "A panel of economists discuss Q3 GDP data" | `serious` or `neutral` | Formal and measured. If no emotional charge is evident, `serious`; if truly flat, `neutral`. |

---

### `best_listening_context`

**Definition:** When would a listener naturally reach for this episode? This is about format and cognitive load, not topic. Pick 1–4 values.

| Value | What it means |
|---|---|
| `commute` | Good for passive, interrupted listening. Doesn't require note-taking. 20–60 min length typical. |
| `workout` | High energy, motivating, or engaging enough to pass gym time. Usually not heavy on dense information. |
| `deep_work` | Requires focused, uninterrupted attention. Complex arguments, technical depth, or long narratives. |
| `casual_listening` | Low cognitive demand. Good background while relaxing. |
| `cooking` | Short-to-medium length, light enough to follow while doing something else with your hands. |
| `sleep` | Soft, slow, monotone or ambient. Helps wind down. Very rare in podcasts — use sparingly. |
| `social` | You'd listen with someone else or share it immediately after. Makes for good conversation fodder. |
| `learning` | Explicitly educational content you'd want to absorb, possibly re-listen to, or take notes on. |

**Decision rules:**

- `deep_work` and `workout` almost never co-occur — a dense technical lecture isn't gym listening.
- `sleep` should only be used if the description explicitly signals slow, meditative, or ambient content. Do not assign it to calm episodes generally.
- A 3-hour Joe Rogan conversation is `commute` + `casual_listening`, not `deep_work`, even if topics are sometimes serious — the format is relaxed and wandering.
- A 45-minute explainer on neural network architecture is `deep_work` + `learning`, not `commute`, even if the length fits a commute.
- An episode with guests sharing wild stories is `social` (you'd talk about it later).

**Examples:**

| Episode type | Labels |
|---|---|
| 90-min founder interview, candid and wide-ranging | `commute`, `casual_listening` |
| Deep-dive on quantum computing fundamentals, lots of math | `deep_work`, `learning` |
| Comedy episode: two hosts riff on pop culture | `workout`, `casual_listening`, `cooking` |
| Meditation guide / sleep story crossover podcast | `sleep`, `casual_listening` |
| Breaking news analysis of a major political event | `commute`, `social` |
| 20-min daily briefing on markets | `commute`, `cooking` |

---

### `primary_topics`

**Definition:** The 1–3 topics that are central to what the episode is actually about. These should be the topics a listener would use to find this episode, or describe it to a friend.

Pick from this taxonomy:

```
Technology:   artificial_intelligence, software_engineering, cybersecurity, hardware, startups_and_vc, data_science,
              surveillance_and_privacy
Science:      neuroscience, physics, biology, medicine, astronomy, climate_and_environment,
              mathematics, planetary_science, paleontology
Business:     entrepreneurship, investing, marketing, leadership, economics, productivity
History:      ancient_history, modern_history, military_history, political_history, cultural_history,
              mythology
True Crime:   cybercrime, true_crime
Health:       nutrition, fitness, mental_health, sleep, longevity
Philosophy:   ethics, philosophy_of_mind, spirituality
Comedy:       comedy, satire
Personal Dev: relationships, personal_finance, career, habits_and_mindset
Culture:      politics, media_and_journalism, social_issues, sports, arts_and_entertainment,
              political_commentary
```

**Decision rules:**

- Maximum 3 primary topics. If you want more, you are probably not filtering hard enough. Ask: "What is this episode *primarily* about?"
- When a guest brings personal context to a different domain, let the primary topic reflect the episode's main subject, not the guest's biography. A startup founder discussing mental health: `mental_health` is primary if that's the episode's core subject; `entrepreneurship` is primary if the mental health angle is one thread in a broader founder story.
- **Cross-vertical episodes:** Pick the topic the *host frames the episode around*. Clues: the episode title, the first sentence of the description, and any explicit "today we discuss X" language.
- `startups_and_vc` vs `entrepreneurship`: Use `startups_and_vc` when the episode is explicitly about the startup ecosystem, venture funding rounds, or VC dynamics. Use `entrepreneurship` when it's about building a business more generally (including non-tech businesses).
- `true_crime` vs `cybercrime`: If a crime episode is specifically about a hack, data breach, or tech-based fraud, use `cybercrime`. Use `true_crime` for non-tech crimes.
- `cybersecurity` vs `surveillance_and_privacy`: `cybersecurity` = hacking, defense, vulnerabilities, security engineering. `surveillance_and_privacy` = who is watching whom, data collection by governments/corporations, digital privacy rights. Can co-occur.
- `politics` vs `political_commentary`: `politics` = policy analysis, elections, legislation, governance, neutral or journalistic framing. `political_commentary` = explicitly partisan opinion, punditry, editorial framing, host expressing strong political views. Dan Bongino = `political_commentary`; The Daily = `politics`.
- `ancient_history` vs `mythology`: `ancient_history` = documented historical events and people (wars, civilizations, rulers). `mythology` = legends, myths, folklore — stories whose truth is not asserted (Jason & Argonauts, Greek gods, creation myths). Can co-occur as primary + secondary.
- `astronomy` vs `planetary_science`: `astronomy` = stars, galaxies, cosmology, space observation. `planetary_science` = planets, moons, Earth's geology, solar system formation, asteroid impacts. An episode about Earth's ancient water or dinosaur extinction = `planetary_science` or `paleontology`, not `astronomy`.
- `paleontology` vs `ancient_history` vs `biology`: `paleontology` = prehistoric life (dinosaurs, fossils, mass extinctions, deep time). `ancient_history` = human history (civilizations, culture, warfare). `biology` = living organisms and processes. Dinosaur episodes = `paleontology`; Greek civilization = `ancient_history`.
- `mathematics` vs `physics`: `mathematics` = pure math, statistics, probability, mathematical reasoning. `physics` = physical laws, forces, particles, energy. An episode where the primary content is mathematical reasoning or numerical exploration = `mathematics`.

**Examples:**

| Episode description signal | Primary topics |
|---|---|
| "How Sam Altman thinks about the future of AI" | `artificial_intelligence`, `startups_and_vc` |
| "A startup founder opens up about her burnout and therapy journey" | `mental_health`, `entrepreneurship` |
| "The history of the US opioid epidemic" | `modern_history`, `medicine` |
| "How gut bacteria shape your mood, focus, and immune system" | `biology`, `nutrition` |
| "Comedian breaks down the absurdity of political debates" | `comedy`, `politics` |
| "Inside the hack that took down a national power grid" | `cybercrime`, `cybersecurity` |
| "Marcus Aurelius and the philosophy of resilience" | `philosophy_of_mind`, `habits_and_mindset` |

---

### `secondary_topics`

**Definition:** Topics that appear meaningfully in the episode but are not the primary focus. Pick 0–5, all different from `primary_topics`.

**Decision rules:**

- Do not pad. If only 1 secondary topic is clearly present, pick 1. Zero is a valid answer.
- A topic must be more than a passing mention to qualify. It should occupy at least a few minutes or a distinct segment.
- If you are assigning 5 secondary topics, stop and ask whether some of those should be primary instead.

---

### `difficulty`

**Definition:** How much prior knowledge does a listener need to follow and benefit from this episode?

| Value | What it means |
|---|---|
| `beginner` | No prior knowledge needed. Concepts are explained from scratch. A curious 16-year-old could follow along. |
| `intermediate` | Some familiarity with the domain is assumed but technical depth is light. A generally well-read person who follows news in the area would be fine. |
| `advanced` | Deep domain expertise is assumed. The host/guest skips foundational concepts. Listeners without background will be lost. |

#### The hardest distinction: `intermediate` vs `advanced`

Use this rule: **Does the episode define its core terms?**

- If the host explains what "Series A funding" is, the audience is `beginner` or `intermediate`.
- If the host says "post-Series A, you need to think about your PMF metrics and burn multiple" without defining those terms, it's `advanced` for a general audience — but if it's a pure startup podcast with a specific audience, it may still be `intermediate` for *that* audience.

**Calibrate to the general listener, not the superfan.** Most podcast audiences are `intermediate` — curious and reasonably informed but not experts.

Signals that push toward `advanced`:
- Technical jargon used without definition
- Mathematical or statistical concepts discussed without simplification
- Assumes the listener has read a specific book, paper, or knows a specific person's prior work
- Episode explicitly says "this one's for practitioners" or similar

Signals that push toward `beginner`:
- "For anyone who's never heard of X..."
- Heavy use of analogies and simplification
- Guest spends time explaining basics before going deeper

**Examples:**

| Scenario | Difficulty |
|---|---|
| "Investing 101: what is a stock?" | `beginner` |
| "How to think about portfolio diversification" (assumes listener knows what stocks/bonds are) | `intermediate` |
| "Factor investing: how Fama-French three-factor model beats naive beta" | `advanced` |
| "What is machine learning?" episode | `beginner` |
| "Practical guide to fine-tuning open-source LLMs" | `advanced` |
| "How GPT works, explained with analogies" | `intermediate` |

---

### `format`

**Definition:** The structural format of the episode.

| Value | What it means |
|---|---|
| `interview` | One or two hosts interviewing one or more guests. Guest-driven content. |
| `solo_monologue` | Single host speaking alone, no guests. |
| `panel_discussion` | Three or more participants (guests and/or hosts) in roundtable discussion. |
| `narrative_storytelling` | Produced, scripted storytelling with narration, often includes sound design. Serial podcasts often use this. |
| `debate` | Structured disagreement between two or more people with opposing positions. |
| `educational_lecture` | Structured teaching, usually solo or lightly conversational, with a clear lesson arc. Often uses prepared content. |

**Decision rules:**

- If in doubt between `interview` and `panel_discussion`: 2 participants total = `interview`; 3+ = `panel_discussion`.
- `educational_lecture` vs `solo_monologue`: A solo episode that is conversational and personal is `solo_monologue`. A solo episode that teaches a structured topic (like a mini-course) is `educational_lecture`.
- `narrative_storytelling` usually appears in shows like Serial, Radiolab, This American Life — produced audio journalism. If it reads like a story with a narrative arc and production elements, use this.

---

### `summary_one_sentence`

**Definition:** One sentence (max 200 characters) that captures what this specific episode is about. Must be grounded entirely in what the description says.

**Rules:**

- Do not invent facts, guest credentials, or outcomes not stated in the description.
- Do not write a generic sentence that could apply to any episode of the same show.
- Do not start with "In this episode..." — start with the subject.
- If the description is sparse, write only what you can confirm. "A conversation with a cybersecurity researcher about recent high-profile data breaches" is fine even if vague — it reflects the source.

**Examples:**

| Description says | Good summary | Bad summary |
|---|---|---|
| "We talk to Dr. Jane Smith about how sleep deprivation affects cognition" | "Dr. Jane Smith explains how sleep deprivation impairs cognitive function." | "The world's leading sleep expert reveals the hidden dangers of modern insomnia." (embellished) |
| "A look back at the 2008 financial crisis and what we got wrong" | "Retrospective on the 2008 financial crisis and the policy mistakes that shaped its aftermath." | "In this episode, we discuss finance." (too generic) |
| "Chris and Jamie discuss what they've been reading" | "Chris and Jamie share recent reads and discuss what they found compelling." | "Two literary experts break down the year's best books." (invented credentials/scope) |

---

### `key_entities`

**Definition:** Named people, companies, books, places, research papers, or products explicitly mentioned in the description or title. Maximum 10.

**Rules:**

- Only include entities that are actually named in the text. Do not add entities you associate with the topic.
- Include: guest names, companies discussed, books referenced, specific studies cited, notable places if they are thematic (not just the city where the podcast was recorded).
- Exclude: generic terms, topic categories, the podcast's own name.
- Format as a list: `["Name One", "Company X", "Book Title"]`

**Examples:**

- "We sit down with Sam Altman to discuss OpenAI's GPT-4 launch" → `["Sam Altman", "OpenAI", "GPT-4"]`
- "A deep dive into Walter Isaacson's biography of Elon Musk" → `["Walter Isaacson", "Elon Musk"]`
- Episode about machine learning in general, no names → `[]`

---

### `content_warnings`

**Definition:** Flags that help listeners decide whether the episode is appropriate for their context (e.g., driving with kids, sensitive personal topics). Leave empty if none apply.

**When to add a warning:**

- Explicit language (profanity, sexual language)
- Graphic medical or clinical content (detailed descriptions of injuries, surgeries, illness)
- Violence or trauma (war, abuse, assault discussed in detail)
- Strong political opinions (explicitly partisan, polemical framing)
- Disturbing true crime details (graphic crime scene descriptions)
- Eating disorder or self-harm content
- Death/grief discussed in personal or graphic detail

**Format:** A list of short phrases: `["explicit language", "graphic violence", "trauma discussion"]`

**Rules:**

- Only flag what is signaled in the description. If the description says "explicit" or has a Parental Advisory note, flag it. If the description is general and neutral, do not flag based on topic alone.
- A war history episode is not automatically flagged for violence unless the description signals graphic content.
- A mental health episode is not automatically flagged unless it signals discussion of self-harm or trauma.

---

### `is_sponsored`

**Definition:** `true` if the episode description or title explicitly mentions paid sponsorships or advertisements.

**Rules:**

- **Explicit only.** Words like "brought to you by," "sponsored by," "this episode is presented by," "ad-free version available," or named sponsor brands in an ad context count.
- Do NOT infer sponsorship from the show being well-known, commercial, or from the host's brand deals.
- A host mentioning their own product or book is NOT a sponsorship — that is self-promotion.
- "Support us on Patreon" is NOT a sponsorship — that is listener support.
- The description mentioning a company the guest works at is NOT a sponsorship.

**Examples:**

| Signal | `is_sponsored` |
|---|---|
| "This episode is brought to you by Squarespace" | `true` |
| "Sponsored by Calm and Athletic Greens" | `true` |
| "Get the ad-free version on Patreon" | `false` (the Patreon reference implies ads exist but this isn't an explicit sponsor mention in the description) |
| "My guest today is the CEO of Stripe" | `false` |
| "Check out my new book at [link]" | `false` |
| Description includes "[Ad] MasterClass..." | `true` |

---

### `labeler_confidence`

**Definition:** How confident are you that your labels accurately reflect the episode content?

| Value | When to use |
|---|---|
| `high` | The description gave you enough information to make clear, well-grounded decisions for all major fields. |
| `medium` | One or two fields required a judgment call, or the description was somewhat vague in places. |
| `low` | The description was too sparse, ambiguous, or misleading to be confident in multiple fields. You made your best guesses but they could be wrong. |

**Rules:**

- When `low`, still complete all fields — the label is better than a blank.
- `low` does not mean the episode is bad; it means the *description* didn't give you enough to work with.
- If the description is one sentence or fewer and covers a broad topic, default to `low`.

---

## Quick-Reference Cheat Sheet

### mood — pick one
```
energetic    = excitement drives the energy (pumped up)
calm         = unhurried, relaxed delivery
intense      = stakes or depth drives the energy (locked in)
melancholic  = loss, regret, wistfulness
humorous     = jokes are the point
serious      = formal, sober, weighty (not emotionally charged)
inspirational = motivational, uplifting, transformative journey
neutral      = no tonal signature (last resort)

KEY: energetic vs intense → enthusiasm vs stakes
```

### best_listening_context — pick 1–4
```
commute          = passive, interrupted listening OK
workout          = energizing, not cognitively dense
deep_work        = requires full, uninterrupted attention
casual_listening = low cognitive demand, good background
cooking          = short-medium, light enough to multitask
sleep            = slow/ambient (rare — use sparingly)
social           = you'd discuss it with someone immediately after
learning         = you'd want to take notes or re-listen
```

### primary_topics — pick 1–3
```
Technology:   artificial_intelligence, software_engineering, cybersecurity, hardware, startups_and_vc,
              data_science, surveillance_and_privacy
Science:      neuroscience, physics, biology, medicine, astronomy, climate_and_environment,
              mathematics, planetary_science, paleontology
Business:     entrepreneurship, investing, marketing, leadership, economics, productivity
History:      ancient_history, modern_history, military_history, political_history, cultural_history,
              mythology
True Crime:   cybercrime, true_crime
Health:       nutrition, fitness, mental_health, sleep, longevity
Philosophy:   ethics, philosophy_of_mind, spirituality
Comedy:       comedy, satire
Personal Dev: relationships, personal_finance, career, habits_and_mindset
Culture:      politics, media_and_journalism, social_issues, sports, arts_and_entertainment,
              political_commentary

KEY DISTINCTIONS (v1 additions):
  politics vs political_commentary  → journalistic/neutral vs partisan/punditry
  cybersecurity vs surveillance_and_privacy → defense/hacking vs who-watches-whom
  ancient_history vs mythology → documented fact vs legend/myth
  astronomy vs planetary_science → stars/cosmos vs planets/Earth/solar system
  paleontology → dinosaurs/fossils/mass extinction (not ancient_history, not biology)
  mathematics → pure math/stats/probability (not physics)

CROSS-VERTICAL: What does the HOST frame as the episode's subject?
```

### difficulty — pick one
```
beginner     = explains from scratch, anyone can follow
intermediate = assumes general familiarity, not expertise
advanced     = skips basics, assumes domain expertise

KEY: Does the episode define its core terms? No → lean advanced.
```

### format — pick one
```
interview              = host interviews guest(s)
solo_monologue         = single host, no guests, conversational
panel_discussion       = 3+ participants in roundtable
narrative_storytelling = scripted, produced audio journalism
debate                 = structured disagreement with opposing positions
educational_lecture    = structured teaching arc, even if solo
```

### is_sponsored
```
TRUE:  "brought to you by X", "sponsored by X", named brand in ad context
FALSE: host's own book/product, Patreon, guest's employer, inferred ads
RULE:  Explicit in description only. When in doubt → false.
```

### labeler_confidence — pick one
```
high   = clear description, confident on all fields
medium = one or two judgment calls or mild vagueness
low    = sparse description, multiple fields are guesses
```
