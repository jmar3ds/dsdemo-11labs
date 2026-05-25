# PT-BR Voice Output Quality Rubric

**Companion to:** [`deployment_playbook.md`](deployment_playbook.md), Section 7 (Success metrics, MOS line); [`architecture.md`](architecture.md), STT and TTS components
**Used by:** Magalu CX QA panel (3 reviewers, weekly cadence during pilot) + ElevenLabs DS during model evaluation and voice selection
**Output:** Each sample scored on 8 dimensions, 1-5 scale, anchored at 1, 3, and 5. Sample-level score is the mean. Voice-level score is the median across at least 20 samples.

This rubric is the working version of what "voice quality MOS" means in the playbook. Generic MOS is a single 1-5 number. Useful for trending but useless for diagnosis. Eight dimensions give the reviewer enough to diagnose: this voice is a 3.2 because pacing is dragging and emotional fit is off, even though intelligibility is fine.

## How to score

1. **Score blind where possible.** QA reviewer sees the script text but not the voice persona name, so Luiza and Rafael are evaluated on the same dimensions without persona-halo bias.
2. **Score at the utterance level.** The customer hears the sentence.
3. **Score against the use case.** A 5 on Naturalness for a card-block confirmation looks different from a 5 on Naturalness for a celebratory onboarding line.
4. **Use 3 as the honest middle.** 3 means "acceptable for production, workmanlike." 1 means "send back to the drawing board." 5 means "noticeably good, audio I would happily send to the customer demo."
5. **Anchor disagreements.** If two reviewers disagree by more than 1 point on a dimension, they listen together once and reconcile or flag for DS review.

A sample below 3.5 on any dimension triggers review. A voice persona below 4.0 median across all dimensions triggers a model or voice swap decision per the playbook risk register.

---

## Dimensions

### 1. Naturalness

How human does this sound across the full utterance?

- **1.** Obviously synthetic. Robotic cadence, audible TTS signature, breaks the customer out of the conversation in the first three seconds.
- **3.** Acceptable. A reasonable listener might suspect it is synthetic but it does not break the flow. The kind of voice the customer would not complain about, but would not praise either.
- **5.** Indistinguishable from a recorded human at conversational length. Reviewer would have to be told it is TTS. Pauses, breath, intonation all read as a person speaking.

### 2. Pacing

Does the speech move at the speed a Brazilian customer would expect for the moment?

- **1.** Drags or rushes through the whole utterance. Customer would interrupt, or get bored, or miss a key word because it flew past.
- **3.** Generally appropriate pace, with one noticeable hiccup (a too-long pause, a phrase that compresses). Listener notices but adapts.
- **5.** Pacing matches the use case throughout. Greeting is unhurried, balance readback gives the customer time to register numbers, card-block confirmation is crisp. Feels like the voice is reading the room.

### 3. PT-BR regional appropriateness

Does this sound specifically like Brazilian Portuguese to a Brazilian listener?

- **1.** Reads as PT-PT, generic LatAm, or English-influenced "Brazilian." A Brazilian would clock it as foreign in the first sentence. Vocabulary, intonation, or accent betrays the wrong region.
- **3.** Recognizably Brazilian, with one or two small giveaways (an unusual word choice, a slightly off vowel) that a Brazilian listener would notice but not call out.
- **5.** Sounds like someone from São Paulo or Rio talking on the phone. Vocabulary, intonation, and accent are all of-a-piece. A reviewer in Bahia or Recife would identify it as paulistano/carioca but not as foreign.

### 4. Emotional fit (matches the moment)

Does the affect of the delivery match the affect the customer needs in this exchange?

- **1.** Energy is wrong for the moment. Cheerful on a fraud alert. Cold on a welcome. Neutral on a customer in distress. The voice is fighting the script.
- **3.** Generally appropriate, with one moment where the energy slips (a too-cheerful "obrigada" after a difficult exchange, a too-warm tone on a card-block confirmation).
- **5.** Affect tracks the customer's likely emotional state throughout. Warmth on greeting, focused calm on a card block, empathy on a dispute, lightness on a closing. The voice is doing emotional work.

### 5. Intelligibility

Can a listener understand every word the first time, in real listening conditions (phone audio, WhatsApp compression, ambient noise)?

- **1.** Listener has to replay or guess. Words mumble, blend, or get swallowed. Numbers and proper nouns are especially vulnerable.
- **3.** Understandable on first listen with attention. One or two words might benefit from a replay, especially numbers or proper nouns under compression.
- **5.** Every word is clear on first listen, including monetary values, document numbers, names, and English-origin terms. Holds up under phone-quality audio.

### 6. Technical artifacts (clicks, pops, drift, noise)

Are there audible artifacts (clicks, pops, hum, prosodic drift across long utterances, model glitches) that would interrupt the listener?

- **1.** Multiple noticeable artifacts in a single utterance. A click, a phantom breath, a sudden pitch wobble, an obvious "model glitch" moment.
- **3.** Clean for most of the utterance, with one noticeable artifact (a single click between phrases, a slight drift at the end of a long sentence).
- **5.** No audible artifacts. Listener attention is on content throughout. Clean across utterance length up to ~15 seconds.

### 7. Code-switching handling (proper nouns in English, technical terms)

How well does the voice handle words that are not natively Brazilian Portuguese: brand names, English-origin tech terms, foreign proper nouns?

- **1.** Mispronounces English brand names or tech terms in a way that betrays the model. "PIX" rendered as English "pix," "WhatsApp" as a stilted reading, "iPhone" mangled. Breaks immersion.
- **3.** Handles common terms ("WhatsApp," "PIX," "app") fluently but stumbles on less common ones (lesser-known brand names, longer English phrases). Acceptable but noticeable.
- **5.** Handles English-origin terms with the natural BR-Portuguese inflection a real Brazilian speaker would use. "WhatsApp" sounds the way a Brazilian friend would say it on the phone. Proper nouns in English are confident but Brazilianized.

### 8. Prosody (stress and intonation)

Does the voice put stress on the right syllables and the right words for what is being said?

- **1.** Stress and intonation are wrong often enough to change meaning or feeling. Questions sound flat. Important words go unstressed. Listener has to mentally re-parse.
- **3.** Stress is right most of the time, with one phrase per utterance where intonation feels off. Listener notices but understands.
- **5.** Stress and intonation are correct and expressive throughout. Questions rise, lists have list-cadence, the important word in the sentence gets the emphasis a human speaker would give it.

---

## Worked example

Sample: `balance_check_01` rendered by Luiza (warm_female_br).

| Dimension | Score | Notes |
|---|---|---|
| Naturalness | 4 | Reads as human across the whole line, with a slight TTS signature on the closing question. |
| Pacing | 5 | "Só um instante" lands at the right speed, the monetary value gives the listener time to register. |
| Regional appropriateness | 4 | Paulistano-leaning, one slightly closed vowel a carioca reviewer noted. |
| Emotional fit | 5 | Warm, attentive, ends on engagement. |
| Intelligibility | 5 | Every digit and centavos value clear on first listen. |
| Technical artifacts | 4 | One barely-audible click between "consulto" and "Pronto." |
| Code-switching | n/a (no English terms in this sample) | Score omitted, sample-level mean computed over remaining dimensions. |
| Prosody | 5 | Stress on "atual" and "saldo" is correct, the closing question rises naturally. |
| **Sample mean** | **4.57** | Above ship threshold. |

Voice-level decision: a single sample at 4.57 is not enough to draw conclusions. Score Luiza across at least 20 representative samples spanning all in-scope use cases before any production decision.

## Notes for the QA panel

- **Score in PT-BR listening conditions.** Headphones for diagnosis, phone speaker for the final intelligibility check. WhatsApp audio compression matters; a sample that scores 5 on intelligibility through studio monitors can drop to 3 on a phone speaker in a noisy room. Test where the customer listens.
- **Score across utterance length.** A voice that nails a 5-second greeting can drift on a 25-second explanation. Sample length distribution should match production traffic.
- **Re-score on every model version change.** Pinned model version is in `src/config.py`. Treat every upgrade as a release candidate. Re-score the full sample set before promoting.
- **Disagreements are signal.** If two reviewers diverge on Regional Appropriateness, that often means the sample is on the edge of acceptability and would benefit from a wider listener panel before any production decision.
