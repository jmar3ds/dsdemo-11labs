# Fale com a Lu da Magalu: Voice AI Deployment Playbook

**Customer:** Magazine Luiza (Magalu), specifically the WhatsApp da Lu surface
**Engagement:** PT-BR conversational voice agent and voice notification stack for retail customer operations
**Author:** João Marcos dos Santos
**Date:** 2026-05-18
**Status:** Deployment-strategy prototype

> This document is part of a deployment-strategy prototype. It demonstrates how I would approach an ElevenLabs voice AI engagement with Magalu in Brazil. The customer scenario is real (Magalu launched WhatsApp da Lu with voice input in November 2025, with Lu still replying in text), the public sources are cited inline, and the engagement framing is treated as a working hypothesis rather than a signed contract. The discovery questions, architecture, and four-phase rollout are the deliverable. The Python in this repo is supporting evidence.

---

## 1. Executive summary

Magalu has built one of the most recognizable virtual brand personas in the world: Lu, voiced on social by actress and comedian Marianna Armellini, with 31M+ followers across channels. In November 2025 Magalu launched WhatsApp da Lu, a customer-service surface that accepts voice notes from customers but replies in text only (verified by direct chat with Lu in May 2026, and consistent with the absence of any published voice-output partnership across 8+ post-launch articles in Mobile Time, Martech, Exame, and Fast Company Brasil). Brazilians send roughly four times more audio messages than any other country. The asymmetry is the opportunity: customers are already speaking to Lu; Lu cannot yet speak back.

The pragmatic entry point is a Phase 1 voice notification pilot on WhatsApp using a premade ElevenLabs voice (warm female PT-BR, Rachel-style) on `eleven_multilingual_v2`, A/B tested against the text-only baseline on high-frequency outbound notifications: abandoned-cart recovery, order-status updates, delivery ETA, promotional campaigns. It ships fast, requires no talent licensing, produces clean conversion-lift data, and earns the right to Phase 2. Phase 2 (months 2 to 6) introduces a Professional Voice Clone of approved Brazilian voice talent (Marianna Armellini if licensing aligns) as the omnichannel Lu voice across WhatsApp, the Magalu App, and customer service touchpoints, with PT-BR regional dialect coverage. Phase 3 (months 6 to 12) extends Lu's voice into 1,245 physical stores, short-form social, owned-media, and "Pergunta pra Lu," a named voice-driven product-comparison feature. Phase 4 (months 12 to 24) is network effects: Magalu Cloud as ElevenLabs reseller for partner retailers, Spanish Lu for LATAM, English Lu for international shipping, Lu Pay financial-literacy voice. Each phase has an explicit success gate; skipping a gate is not allowed.

The success of the Phase 1 pilot is not the bot answering correctly. It is the bot knowing when to stop. Brazilian customer-service research consistently shows the cost of a voice surface that refuses to escalate is dramatically higher than the cost of one that escalates a winnable case. Our design treats human handoff as a feature and instruments it as a primary metric (handoff quality) rather than a negative one (containment loss).

A 90-day Phase 1 pilot at this scope runs roughly USD 4 to 7K per month of ElevenLabs spend plus internal integration cost. The honest "did this work?" check on day 90 is three numbers read together: conversion lift on voice notifications vs. the text baseline, CSAT delta for voice-touched vs. text-touched cohorts, and incremental cart-abandonment recovery. If voice notifications fail to lift conversion by the agreed-upon floor, or CSAT slips by more than 5 points on the voice cohort, we stop and redesign before Phase 2.

---

## 2. Customer context

Magalu is one of the three largest retailers in Brazil: 30M+ active customers on WhatsApp, 1,245 physical stores nationwide, a marketplace of 100K+ third-party sellers, and a fintech arm (Magalu Pay). Lu is Magalu's virtual brand persona, launched in 2003 as a product-explainer character and now one of the largest virtual influencers on the planet (31M+ followers across Instagram, TikTok, YouTube). Lu's social-media voice is performed by Marianna Armellini, an actress and comedian whose delivery is now inseparable from the brand.

WhatsApp da Lu launched in November 2025 (Mobile Time, Nov 2025; Martech, Nov 2025) as a unified customer-service surface. Customers can send Lu voice notes; Lu replies in text. A direct test in May 2026 confirms outbound is still text-only, and no ElevenLabs partnership or voice-output capability has been announced in any of the 8+ post-launch articles surveyed (Mobile Time, Martech, Exame, Fast Company Brasil).

ElevenLabs has publicly identified WhatsApp as its #1 priority for Brazil in 2026 (Brunno Santos, GM Brasil), with target sectors including financial services, education, entertainment, telecom, healthcare, and retail. The first Brazilian brand campaign on ElevenLabs's reference list is Judite 2.0, a beloved cultural icon revived as an AI voice in partnership with Fábio Porchat. Lu is the next obvious instance of that pattern: a beloved character, an audience already comfortable with the persona, and a surface (WhatsApp) where voice consumption is culturally native.

The pain points and opportunities a Magalu CX and brand leadership team would name:

- **Customer-side asymmetry.** Customers speak; Lu types. The dominant inbound modality for casual BR messaging is not matched on the outbound side. A brand inconsistency Magalu has not yet had a path to resolve.
- **Voice consumption pull.** Brazilians send roughly 4x more audio messages than any other country. Outbound voice notifications on WhatsApp test exceptionally well in retail when delivered in a recognizable voice rather than synthetic neutral TTS.
- **Volume on routine intents.** A meaningful share of inbound is repetitive: where is my order, delivery ETA, can I exchange this, what is the status of my refund. These are the right starting surface: high-frequency, low-ambiguity, getting them right is loyalty rather than risk.
- **Physical-store underutilization for voice.** 1,245 stores are a voice surface Magalu has not yet activated. In-store kiosks with Lu's voice are a brand reinforcement no Brazilian retailer is currently doing at scale.
- **Regulatory weight.** LGPD applies to all voice processing. Consumer-protection regulation (CDC primarily, plus LGPD for data handling) governs retail; the weight is real but materially less heavy than financial services. Magalu Pay activity is the exception and lands in financial-services regulation when it appears.

What Magalu wants from a Phase 1 pilot: a measurable conversion lift on voice notifications, a clean A/B story for the board, and a path to Lu speaking in her own voice that does not compromise brand or talent relationships. What they are rightly worried about: a generic synthetic voice that dilutes Lu's brand equity, talent licensing missteps with Marianna, LGPD exposure on voice processing, and vendor lock-in.

---

## 3. Discovery questions

These are the questions I would walk into a Magalu kickoff with. They are organized to make the customer's reasoning visible before any architecture gets drawn.

### 3.1 Business goals

1. If the Phase 1 pilot succeeds, what changes for CX and growth next quarter? Next year?
2. What is the financial case you take to the CFO: conversion lift on cart recovery, CSAT, cost takeout, all three?
3. What does failure look like that you could still defend internally? What ends the program?
4. Who owns Lu's voice as a brand asset (marketing, brand, talent management)? Who owns its service behavior (CX ops, product, legal)?

### 3.2 Current state

5. Walk me through one real WhatsApp da Lu contact from yesterday: intent, inbound modality (voice note vs. text), Lu's response, time to resolution, customer mood.
6. What percentage of inbound on WhatsApp da Lu is voice notes vs. text? Has that shifted since launch?
7. What is your current containment rate on WhatsApp da Lu by intent?
8. What does QA look like for the current Lu experience? What would the equivalent be for outbound voice and (Phase 2) for a voice-replying Lu?

### 3.3 Technical environment

9. Which WhatsApp Business API provider routes your traffic (Meta direct, Take Blip, Twilio, Sinch)?
10. What is the current Lu orchestration stack? Where would ElevenAgents slot in?
11. What CRM and ticketing system holds the customer context Lu will need (Salesforce Service Cloud, Zendesk, in-house Magalu Cloud)?
12. How do you authenticate customers on WhatsApp? What signals (CPF on file, order ID, device, biometric) are available?
13. Where does Lu's knowledge base live? Structured (catalog, order DB) or unstructured (FAQ, help center)? How is it kept fresh?

### 3.4 Success metrics

14. Which metrics does Magalu leadership already trust for WhatsApp da Lu? Which would they discount as bot-friendly framing?
15. What is the current human-agent CSAT baseline on WhatsApp by intent?
16. What is the current conversion rate on abandoned-cart recovery via WhatsApp text? On delivery-ETA proactive messages? These are the A/B baselines.
17. What is the fully loaded cost of a contact on WhatsApp da Lu today?

### 3.5 Risks and constraints

18. What is your LGPD posture on transcripts and voice recordings: retained, redacted, deleted on close? Your DPO's view on voice biometrics?
19. What does legal consider unacceptable for a voice persona to say without human review (price commitments, return-policy edges, Magalu Pay product mentions)?
20. On talent licensing: scope of Marianna Armellini's current voice rights with Magalu, and appetite to extend to AI cloning on what commercial structure?

The point of 20 questions is not to delay shipping. It is to make sure that when we do ship Phase 1, Magalu recognizes the deployment as theirs.

---

## 4. Recommended use cases

Ranked by effort vs. impact for a retail engagement. Effort is integration complexity. Impact is contact volume reduction plus conversion lift, weighted by intent safety.

| Rank | Use case | Effort | Impact | Reasoning |
|------|----------|--------|--------|-----------|
| 1 | Order status / "cadê meu pedido" | Low | High | Highest single-intent volume on retail WhatsApp. Read-only lookup, voice delivery reassures on delivery anxiety. Safest deployment surface. |
| 2 | Delivery ETA proactive notification | Low | High | Outbound voice note at last-mile handoff and out-for-delivery. Drives CSAT and reduces inbound "cadê meu pedido" volume. |
| 3 | Abandoned-cart recovery | Low | High | The conversion-lift headline. Voice notification with Lu's warmth, clear product reference, single-tap return path. A/B vs. text produces the CFO number. |
| 4 | Product recommendation / "Pergunta pra Lu" prototype | Medium | High | Voice-driven comparison is native to Lu's persona; production is Phase 3. Phase 1 prototypes a narrow vertical on the demo surface only. |
| 5 | Returns and exchanges intake | Medium | Medium | Higher ambiguity than order status. Voice intake works; resolution often needs human review on CDC edge cases. Bot triages, humans close. |
| 6 | Escalation handoff to human attendant | Medium | High | The crucial seam. Voice handoff that names the human, summarizes context, and promises no context-repeat is a CSAT lever. "Camila" pattern in `data/support_scripts.json` is the reference. |
| 7 | Promotional campaigns | Medium | Medium | Outbound voice marketing surface. Conversion-positive, fatigue-risk, requires frequency capping and consent. Phase 1 limited to opted-in cohorts on one campaign. |
| 8 | Magalu Pay financial guidance | Out of scope (Phase 1) | n/a | Hard regulatory wall when it touches advice. Phase 4 reopens under Lu Pay financial literacy with explicit guardrails. |

For Phase 1, ship 1, 2, and 3 first, with 6 as the safety valve. Add 4 as a contained prototype only if the demo surface is needed for a stakeholder review. Five intents is too many to instrument honestly in 90 days.

---

## 5. Voice and model selection

The voice catalog in `data/voice_catalog.json` defines three deliberately distinct profiles. The selection logic for Magalu:

**Primary persona: Luiza (warm_female_br, Rachel voice on `eleven_multilingual_v2`).** The Phase 1 default. Warmth ("tratamento humanizado") is a measurable CSAT lever in BR retail; a warm mid-register female voice reads as approachable in PT-BR without sounding artificial. Luiza is the prototyping voice for outbound notifications, the demo voice for stakeholder reviews, and the placeholder identity until Phase 2 brings in a PVC of approved talent. Luiza is distinct from Lu by design. The naming is deliberate: Magalu's production brand voice must be a PVC of cast or contracted talent.

**Tactical persona: Rafael (neutral_male_br, Adam voice on `eleven_multilingual_v2`).** Used surgically for moments where clarity beats warmth: order-issue confirmations, payment-related readbacks, delivery exception notifications. Grounded mid-register male reads as institutional credibility. Never the default; using Rafael as Lu's primary would break the brand entirely. Used sparingly inside the demo surface to illustrate persona-switching options.

**Onboarding and celebratory persona: Marina (energetic_female_br, Matilda voice on `eleven_multilingual_v2`).** Reserved for positive-affect moments outside the support flow (order shipped, Magalu Ouro reward earned, Magalu Pay savings milestone). Out of scope for Phase 1; pre-selected as the celebration-cell voice in Phase 2 A/B testing.

**Model choice.** `eleven_multilingual_v2` is the Phase 1 default. Best PT-BR prosody across all three voices in our tests; best stability under product-name and price readback (where TTS artifacts erode trust fastest). `eleven_flash_v2_5` is held in reserve for short proactive notifications under 8 seconds and high-traffic conversational turns where time-to-first-audio matters more than expressive range. Model selection is per turn (or per notification template).

**Voice cloning path (Phase 2).** The production Lu voice is a Professional Voice Clone (PVC). PVC is the production tier. Instant Voice Clone (IVC) covers prototyping (~1 minute of reference audio, available across plans); PVC requires ~30 minutes of curated reference audio and the Pro plan, and produces materially higher fidelity, prosodic consistency, and brand-grade stability. No Magalu production deployment ships on IVC. The PVC target, subject to licensing, is Marianna Armellini's voice; the casting alternative is a contracted Brazilian voice actor with comparable range.

### Talent Licensing Note

Phase 2 PVC of Marianna Armellini requires a Magalu-Marianna licensing agreement handled in parallel by Magalu's legal and talent-management teams. ElevenLabs is the technology partner for the voice cloning workflow (intake of reference audio, clone training, version control, usage attestation). The split is clean: Magalu owns the talent relationship and commercial structure with Marianna; ElevenLabs delivers the cloning capability and deployment surface. If licensing scope cannot be extended to AI cloning on acceptable terms, the Phase 2 fallback is a casting process for a contracted voice actor matching the established Lu persona, with the same PVC workflow. Either path is materially better than shipping a production brand on a premade voice.

---

## 6. Integration architecture

The voice surface sits inside a path that starts at a Magalu customer's phone and ends in Magalu's back office. The reference architecture is detailed in `docs/architecture.md`; the deployment-relevant view:

**Entry and delivery points.** WhatsApp Business API (via Take Blip, Twilio, Sinch, or whoever currently routes Lu's traffic) handles both inbound voice notes and outbound voice notifications. Magalu App and CS touchpoints come online in Phase 2. Voice IVR, if retained, is a Phase 2 candidate.

**Speech-to-text.** ElevenLabs Scribe is our primary recommendation for PT-BR transcription on inbound voice notes, pending benchmark against the incumbent (often Google Speech-to-Text or AWS Transcribe in BR stacks) on a held-out set of real accented Magalu recordings, scored against the quality rubric.

**Notification orchestration (Phase 1).** A template-driven outbound pipeline. Magalu's existing notification triggers (cart abandoned, order shipped, out for delivery) call into a TTS templating service that renders the voice note (Luiza voice on `eleven_multilingual_v2`), pushes audio to the WhatsApp Business API, and logs the send for the A/B framework.

**Conversational orchestration (Phase 2 onward).** ElevenAgents handles turn-taking, intent classification, and the agent state machine for the replying-Lu experience. Tool calls (order lookup, delivery status, return initiation, escalation) are HTTPS endpoints into Magalu's existing service mesh. The agent orchestrates; Magalu's services are source of truth.

**Text-to-speech.** ElevenLabs TTS using the model and voice selection above. Audio streams back to the WhatsApp or in-app surface.

**Knowledge base.** A version-controlled corpus of Magalu's product catalog metadata, return policy, delivery SLAs, and approved promotional copy. Read-only for the agent. The agent does not generate new policy language; it cites and paraphrases approved language.

**CRM and order systems.** Real-time read of the authenticated customer's profile, current order state, and contact history. Write of conversation summary and outcome at the end. The voice surface never writes customer-facing fields; it writes a structured `ai_conversation_log` record the human agent reads on escalation.

**Human handoff queue.** The crucial seam. When the voice surface escalates, the conversation, transcript, and AI-generated summary land in the human queue with a named agent assigned (the "Camila" pattern in the support scripts). The human picks up with full context. The voice surface does not negotiate with the customer about whether to escalate.

**Observability.** Every notification, turn, and tool call is logged with intent confidence, latency, audio quality flags, and downstream conversion outcome. This powers Section 7.

---

## 7. Success metrics

A pilot is only as good as the metrics it commits to before launch. The five below are Magalu-defensible (CX and growth leadership would put them on a wall) and bot-honest (they cannot be gamed by a voice surface that simply refuses to escalate or sends notifications nobody hears).

1. **Conversion lift on voice vs. text (A/B), by notification type.** Headline metric for Phase 1. Stat-sig minimum cell sizes set with Magalu Data at Day 0.
2. **Cart-abandonment recovery rate, incremental over baseline.** The CFO number. Recovered carts times AOV, attributable to voice, net of cannibalization.
3. **CSAT, segmented voice-cohort vs. text-cohort, within the pilot region.** Target: within 5 points of text-cohort baseline at worst, lift expected. A 5-point drop triggers redesign; 10-point drop triggers a pause.
4. **NPS uplift on voice-touched cohorts** (rolling 90-day, brand-level). Slower-moving brand-equity read on whether Lu's voice is reinforcing or eroding the persona Magalu has spent two decades building.
5. **Voice quality MOS, weekly by a 3-person QA panel against the rubric in `docs/quality_rubric.md`.** Target: 4.0+ on a 1-5 scale. Below 3.5 on any voice triggers review.

Phase 2 onward adds brand-consistency NPS across channels and CS training cost reduction. Phase 3 adds in-store engagement uplift, seller onboarding completion rate, accessibility NPS. Phase 4 adds B2B deployment revenue and LATAM penetration. Cost per resolved contact (where conversational replies are live) is derived and reported monthly.

---

## 8. Four-phase rollout plan

The phases are gated. Each phase ships only after the prior phase's success gate is met and signed off by Magalu Exec and the ElevenLabs DS jointly.

### Phase 1 (weeks 0 to 4): Voice Notification Pilot

Voice notifications on WhatsApp for abandoned-cart recovery, order updates, delivery ETA, and one promotional campaign. Premade Luiza (Rachel) on `eleven_multilingual_v2` as proof-of-concept. A/B against text-only baseline. Cohort scoped to one region (likely São Paulo) and one product vertical to start. Expansion is metric-gated, with no calendar pressure. **Success gate:** conversion lift, open/listen rate, engagement uplift meet the floor agreed at Day 0. Gate passed unlocks Phase 2.

| Day | Milestone | Owner | Dependencies |
|-----|-----------|-------|--------------|
| Day 0 | Kickoff, discovery questions answered, A/B baselines locked | Magalu CX VP + ElevenLabs DS | Discovery interviews completed in week prior |
| Day 7 | Voice catalog reviewed, Luiza approved as Phase 1 prototype voice | Magalu Brand + CX | Sample audio reviewed in shared session |
| Day 14 | Notification templates drafted, legal review on CDC and LGPD wording | Magalu Legal + CX Ops | Draft from ElevenLabs DS |
| Day 21 | A/B framework live, pilot cohort defined, observability instrumented | Magalu Eng + Data + ElevenLabs DS | Templates signed off |
| Day 30 | Pilot live, abandoned-cart and order-status voice notifications to 5% of opted-in WhatsApp cohort in pilot region | ElevenLabs DS + Magalu Eng | All above |
| Day 45 | First metrics review. Decision: hold, expand to 15% cohort, or pause | Magalu CX VP + ElevenLabs DS | 2 weeks of clean data |
| Day 60 | Delivery ETA and one promotional template added | ElevenLabs DS + Magalu Eng | Day 45 green light |
| Day 75 | QA panel scoring against quality rubric, weekly cadence locked | Magalu CX QA | QA training session at Day 30 |
| Day 90 | Phase 1 review. Go/no-go for Phase 2 | Magalu Exec + ElevenLabs DS | Full 90-day data set |

### Phase 2 (months 2 to 6): Omnichannel Brand Voice

Cross-channel voice consistency: same Lu voice on WhatsApp, the Magalu App, and customer service touchpoints. PT-BR regional dialect coverage (carioca, paulistano, nordestino, gaúcho) so Lu sounds local where she lands. **Professional Voice Clone (PVC) of approved Brazilian voice talent, Marianna Armellini if licensing aligns, contracted alternative if not.** Talent licensing handled in parallel by Magalu's legal and talent teams (see Section 5, Talent Licensing Note). CS agent training material voice-cloned for internal consistency (low risk, internal use only). **Success gate:** brand-consistency NPS and CS training cost reduction. Gate passed unlocks Phase 3.

### Phase 3 (months 6 to 12): Voice Goes Everywhere

Lu's voice extends across Magalu's full surface area: in-store kiosks across 1,245 physical stores (an underutilized voice surface at Brazilian retail scale); **"Pergunta pra Lu"** (also "Lu, me ajuda escolher"), a voice-driven product-comparison feature where customers ask Lu to compare two or three options aloud and get a spoken recommendation grounded in product attributes and reviews (named because this is the moment Lu becomes a shopping companion, beyond the notification-voice role); Lu-voiced short-form content at scale on TikTok and Reels through ElevenLabs's content workflow; owned-media voice (Magalu Radio intros, podcast intros, branded audio); marketplace seller onboarding voice tutorials scaling guidance to 100K+ third-party sellers; accessibility surfaces (visually impaired navigation, elderly-friendly UX where reading is friction).

**Success gate:** in-store engagement uplift, seller onboarding completion rate, accessibility NPS. Gate passed unlocks Phase 4.

### Phase 4 (months 12 to 24): Network Effects and Expansion

Magalu Cloud as ElevenLabs reseller for partner retailers (new B2B revenue line leveraging Magalu's partner ecosystem); Spanish Lu for LATAM expansion (Mexico, Argentina, Chile, Colombia), starting where Magalu's logistics or marketplace footprint is already exploratory; English Lu for international shipping and cross-border marketplace inquiries; financial literacy via Lu Pay with strict guardrails on advice vs. education, governed by Phase 1's escalation patterns extended to financial intent.

**Success gate:** B2B voice deployment revenue and LATAM market penetration.

The dependencies pattern is where deployments die. Phase 2 gates on Phase 1's conversion-lift data and the parallel talent licensing closing. Phase 3 gates on Phase 2's omnichannel brand-consistency proof. We do not skip phases to hit a calendar.

---

## 9. Risk register summary

Ten material risks are catalogued in `docs/risk_register.md` with likelihood, impact, mitigation owner, and approach. Headline risks for executive visibility:

- **Voice quality drift** as the model is updated (mitigation: pinned model version, quarterly re-evaluation against the rubric).
- **PII leakage** in transcripts or logs (mitigation: structured redaction at the logging layer, LGPD-compliant retention policy).
- **Hallucination on product, price, or policy claims** (mitigation: read-only RAG over Magalu's approved catalog and policy corpus, hard refuse-and-escalate triggers in the system prompt, legal pre-approval of any new utterance class).
- **Escalation failure** where the voice surface refuses to hand off cleanly (mitigation: customer-initiated escalation always honored, confidence threshold tuned conservatively, named human agent in the handoff).
- **Regulatory exposure under LGPD and applicable consumer-protection regulation (CDC primarily, with financial-services scope when Magalu Pay enters in Phase 4)** (mitigation: conversation classification at intake, automatic routing of regulated intents to human-only paths).
- **Brand dilution risk** if Phase 1 premade Luiza is allowed to bleed into production-brand contexts (mitigation: explicit framing of Luiza as prototyping voice, no Luiza in customer-facing Phase 2 surfaces, PVC ready before Lu replies in voice).
- **Talent licensing slippage** delaying Phase 2 (mitigation: licensing tracked as a parallel critical path from Day 0, casting-alternative contingency identified by Day 60).

The register is a living document, reviewed in every monthly steering meeting.

---

## 10. Cost estimate (illustrative)

Illustrative, based on ElevenLabs published pricing as of 2026-05 and assumed Phase 1 traffic. Not a quote.

**Phase 1 scope (Day 30 to 90, 5% of opted-in WhatsApp cohort, scaling to 15% by Day 60):**

- Voice notification volume: ~120K monthly outbound voice notes at peak (~400 chars each, ~50M chars/month)
- ElevenLabs TTS at Creator/Pro tier with overage: ~USD 1,500 to 3,000/month
- ElevenAgents (limited, escalation prototypes only): ~USD 500 to 1,000/month
- ElevenLabs Scribe STT (if used for inbound voice-note pilot): ~USD 1,000 to 2,500/month

**Phase 1 total ElevenLabs spend, illustrative: USD 4,000 to 7,000/month at peak.**

Magalu-side integration cost (engineering, QA panel, legal review, A/B framework) is ~0.5 to 0.75 FTE for 90 days. Phase 2 cost expands materially with PVC training and omnichannel scope; that envelope is sized at the Day-90 review with actual Phase 1 numbers in hand. The unit-economics question for Phase 1 is whether conversion lift on abandoned-cart recovery and deflection of "cadê meu pedido" volume covers the spend at a comfortable margin. At Magalu retail unit economics, even a modest single-digit-percent lift on cart recovery clears the envelope with room. We produce a real unit-economics view at Day 60.

---

## 11. Commercial structure

Three deal structures I'd propose to Magalu at the Day-60 Phase 1 review. The read here is mine, the call belongs jointly to Magalu's commercial team and ElevenLabs's account team.

### Option A: Hybrid floor-plus-upside (my recommendation)

ElevenLabs implementation fee plus license at a defended floor, plus a per-recovered-cart share over the agreed text-only baseline. Sized so the floor protects ElevenLabs from a slow ramp while the share aligns both teams on the conversion lift. Magalu retail is margin-sensitive, so a full outcome-share asks for more commercial trust than Day 60 can carry. Equally, a fixed license alone disconnects ElevenLabs from the upside Magalu earns. The hybrid carries both pressures.

Practically: a defended floor sized around ~80% of the illustrative monthly spend in Section 10, with the share rate tuned to capture 15-25% of attributable cart-recovery lift over the text baseline. Six-month minimum term so the model amortizes against expected Phase 2 growth.

### Option B: Outcome-based on cart-recovery lift

Pure share of incremental conversion over baseline, with no implementation or license fee. The highest alignment story for Magalu's CFO and the cleanest framing for the board. The cost: ElevenLabs takes on full ramp risk. I'd consider this only when two conditions hold together. Magalu's CFO wants minimum upfront commitment, and the Phase 1 numbers are clean enough to defend a share rate that covers the full spend envelope. Share rate sizing typically 20-35% of incremental lift, with a six-month minimum term.

### Option C: Implementation fee + license

Standard ElevenLabs structure: scope-priced implementation plus recurring license. The fallback if procurement is conservative and the conversion-lift narrative still needs to be earned through Phase 2. The lowest-risk structure for ElevenLabs, the highest-friction sale internally at Magalu, since there is no commercial alignment story for the CFO at the point of signature.

### Talent licensing as parallel critical path

Phase 2 PVC depends on a licensing agreement with Marianna Armellini's representation. I'd open that conversation from Day 0 of Phase 1, treating licensing as the longest pole on the Phase 2 critical path. Magalu's legal and talent teams own the relationship; my posture is technical interpreter, helping them understand what PVC means commercially (rights scope, derivative usage, version control, expiration windows, fallback talent options). The licensing structure folds into whichever pricing option Magalu and ElevenLabs land on, with PVC rights treated as a separate commercial line from the platform agreement.

### GTM partnership posture

The DS role here sits next to the ElevenLabs AE, RevOps, and legal on the Magalu account team. I'd own the use-case-to-deal-structure conversion in discovery and partner on commercial-terms negotiation. Translating Magalu's CX and Brand language into commercial structures the ElevenLabs AE can close is part of the work, as is helping Magalu's procurement and legal teams understand the structure when ElevenLabs's commercial paper crosses their desk.

---

## 12. What we would measure on day 90

The honest "did this work?" check for Phase 1 is three numbers in a sentence:

> On day 90, voice notifications shipped to X% of the opted-in WhatsApp cohort, lifted conversion on abandoned-cart recovery by Y percentage points over the text baseline, and CSAT for the voice-touched cohort was Z points relative to the text-cohort baseline.

Decision tree:

- **Y meets floor AND Z within 5 points of baseline AND MOS above 4.0:** we expand. Phase 2 begins, talent licensing closes on the parallel track, PVC training kicks off.
- **Y meets floor but Z more than 5 points below baseline:** voice is converting but eroding sentiment. Pause expansion, audit notification tone, frequency, consent flow, redesign before Phase 2 sign-off.
- **Y below floor but Z and MOS healthy:** voice is well-received but not driving conversion. Refine copy, expand to delivery ETA and one promotional template, second 30-day window before Phase 2 decision.
- **Z more than 10 points below baseline OR MOS below 3.5:** stop Phase 1, post-mortem, decide continue or sunset.

None of these outcomes is a surprise. We agreed on them at Day 0, instrumented for them through Day 90, and the day-90 meeting is short because the data already answered the question. Phase 2 and beyond inherit the same discipline: clear gates, measurable outcomes, no calendar-driven promotions.

---

*Document prepared as part of the "Fale com a Lu da Magalu" deployment-strategy prototype. Public page: [joaomarcos-dsworksample-11labs.click](https://joaomarcos-dsworksample-11labs.click/). Repository: [github.com/jmar3ds/dsdemo-11labs](https://github.com/jmar3ds/dsdemo-11labs). Contact: joaomarcos@tuta.io.*
