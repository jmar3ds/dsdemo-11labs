# Fale com a Lu da Magalu: Reference Architecture

**Companion to:** [`deployment_playbook.md`](deployment_playbook.md), Section 6 (Integration architecture)
**Scope:** 90-day Phase 1 pilot, voice notifications on WhatsApp da Lu (abandoned-cart recovery, order status, delivery ETA) for one regional cohort, Luiza premade voice on `eleven_multilingual_v2`
**Status:** Reference architecture. The case study page renders an SVG version; this document is the text counterpart and the source of truth for component-by-component risk ownership.

The voice surface does not exist in isolation. It sits inside a path that starts at a Magalu customer's phone and ends in Magalu's back office. Each component below carries a named deployment risk; the cross-references point back to the corresponding row in [`risk_register.md`](risk_register.md).

Phase 1 is outbound notification-led on WhatsApp da Lu. Phase 2 extends to the Magalu App as a secondary surface and brings the conversational replying-Lu experience online with the production PVC of Marianna Armellini (talent licensing in parallel by Magalu).

## System diagram

```
                          ┌───────────────────────────────────────────────┐
                          │            Magalu Customer Surface            │
                          │                                               │
   ┌──────────────────┐  ┌┴──────────────┐   ┌────────────────────────┐  │
   │  WhatsApp da Lu  │  │  Magalu App   │   │  (Future: in-store     │  │
   │  (Phase 1        │  │  (Phase 2     │   │   kiosks, web,         │  │
   │   primary)       │  │   secondary)  │   │   Magalu Radio,        │  │
   │  voice notes in, │  │   voice in    │   │   Phase 3+)            │  │
   │  voice notif out │  │   Phase 2     │   │                        │  │
   └────────┬─────────┘  └───────┬───────┘   └────────────────────────┘  │
            │                    │                                        │
            │ (Take Blip /       │ (Magalu's mobile                       │
            │  Twilio / Sinch    │  app stack, push +                     │
            │  WhatsApp          │  in-app audio surface)                 │
            │  Business API)     │                                        │
            └─────────┬──────────┘                                        │
                      │                                                   │
                      ▼                                                   │
        ┌──────────────────────────────┐                                  │
        │   Voice gateway (audio in    │                                  │
        │   for inbound voice notes,   │                                  │
        │   audio out for outbound     │                                  │
        │   notifications)             │                                  │
        └──────────────┬───────────────┘                                  │
                       │                                                  │
                       ▼                                                  │
        ┌──────────────────────────────┐                                  │
        │  Speech-to-text (ASR)        │   ◄── ElevenLabs Scribe          │
        │  (inbound voice notes,       │       (primary, PT-BR),          │
        │  Phase 2+ replying Lu)       │       benchmarked vs.            │
        │                              │       incumbent (Google or       │
        │                              │       AWS Transcribe)            │
        └──────────────┬───────────────┘                                  │
                       │ transcript                                       │
                       ▼                                                  │
   ┌──────────────────────────────────────┐                               │
   │  Notification orchestrator (Phase 1) │   ◄── Template-driven         │
   │  + ElevenAgents orchestrator         │       outbound pipeline       │
   │  (Phase 2+: turn-taking, intent,     │       (Phase 1) +             │
   │   state)                             │       ElevenLabs              │
   │                                      │       ElevenAgents           │
   │                                      │       (Phase 2+), system     │
   │                                      │       prompt in              │
   │                                      │       agent_system_prompt.md │
   └──┬────────┬──────────┬────────────┬──┘                              │
      │        │          │            │                                  │
      │ tool   │ RAG      │ confidence │ outbound                         │
      │ calls  │ lookup   │ < threshold│ trigger                          │
      ▼        ▼          ▼            ▼                                  │
 ┌────────┐ ┌────────┐ ┌──────────────┐ ┌──────────────┐                │
 │ Magalu │ │ Knowl. │ │  Human       │ │  Magalu      │                │
 │ CX     │ │ base   │ │  handoff     │ │  notification│                │
 │ stack  │ │ (RAG,  │ │  queue       │ │  triggers    │                │
 │ (CRM,  │ │ read-  │ │              │ │  (cart       │                │
 │ orders,│ │ only)  │ │              │ │  abandoned,  │                │
 │ catalog│ │        │ │              │ │  order       │                │
 │)       │ │        │ │  ──► named   │ │  shipped,    │                │
 │        │ │        │ │  human       │ │  out for     │                │
 │        │ │        │ │  agent, AI   │ │  delivery)   │                │
 │        │ │        │ │  summary,    │ │              │                │
 │        │ │        │ │  transcript  │ │              │                │
 │        │ │        │ │  pre-loaded  │ │              │                │
 └────────┘ └────────┘ └──────────────┘ └──────────────┘                │
      │        │                            │                            │
      │ tool   │ cited                      │ trigger                    │
      │ result │ snippet                    │ payload                    │
      └────┬───┘                            │                            │
           │                                │                            │
           ▼                                ▼                            │
   ┌─────────────────────────────────────────────┐                       │
   │ Text-to-speech                              │   ◄── ElevenLabs TTS  │
   │ (PT-BR)                                     │       Luiza (Phase 1) │
   │                                             │       PVC of Lu       │
   │                                             │       (Phase 2+)      │
   │                                             │       eleven_         │
   │                                             │       multilingual_v2 │
   │                                             │       (primary)       │
   │                                             │       eleven_flash    │
   │                                             │       _v2_5           │
   │                                             │       (low-latency    │
   │                                             │       fallback)       │
   └────────────────┬────────────────────────────┘                       │
                    │ audio stream                                       │
                    ▼                                                    │
        back to WhatsApp da Lu / Magalu App surface                      │
                                                                         │
   ┌──────────────────────────────────────────────────────────────────┐  │
   │  Observability + logging                                          │  │
   │  every notification + every turn: intent confidence (where        │  │
   │  applicable), tool calls, latency, audio quality flags,           │  │
   │  redacted transcript, A/B cell assignment, downstream             │  │
   │  conversion outcome                                               │  │
   └──────────────────────────────────────────────────────────────────┘  │
                                                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

## Components

### User entry and delivery points (WhatsApp da Lu primary, Magalu App secondary)

WhatsApp da Lu is the Phase 1 primary surface for both inbound voice notes and outbound voice notifications, routed via Magalu's existing WhatsApp Business API provider (Take Blip, Twilio, Sinch, or whoever currently routes Lu's traffic). The Magalu App comes online as the secondary surface in Phase 2, carrying both push-style voice notifications and the conversational replying-Lu experience. In-store kiosks, web surfaces, Magalu Radio, and the marketplace seller onboarding flow are Phase 3+. The architectural commitment is that Magalu owns the inbound and outbound channels; the voice AI is a participant in their stack.

**Deployment risk this component owns:** Latency at the WhatsApp Business API hop and ingestion variability across providers, plus opt-out and consent handling at the channel boundary. See risks #2 (latency spike) and #9 (regulatory exposure on consent).

### Speech-to-text (PT-BR ASR)

ElevenLabs Scribe is the primary recommendation for PT-BR transcription on inbound voice notes, pending a benchmark against the incumbent (Google Speech-to-Text or AWS Transcribe in most BR retail stacks) on a held-out set of 200+ real, accent-tagged Magalu recordings. The benchmark scores against the Intelligibility and Regional Appropriateness dimensions of [`quality_rubric.md`](quality_rubric.md). In Phase 1 the STT layer supports voice-note intake on the support side; in Phase 2 it becomes load-bearing for the replying-Lu conversational flow. STT errors propagate downstream as intent misclassification and bad tool calls; this component is upstream of everything that matters.

**Deployment risk this component owns:** Accent or regional mismatch in transcription accuracy, which surfaces as agent confusion downstream. See risk #5 (accent or regional mismatch).

### Notification orchestrator (Phase 1) and Conversational agent (Phase 2+)

In Phase 1 a template-driven outbound pipeline renders voice notifications from Magalu's existing notification triggers (cart abandoned, order shipped, out for delivery, one promotional template). The orchestrator owns template selection, A/B cell assignment, frequency capping, and the handoff to TTS. No turn-taking, no intent classification: outbound only, one voice note per trigger event.

In Phase 2 ElevenAgents is added to handle turn-taking, intent classification, agent state, and tool calls for the replying-Lu surface. The system prompt for Luiza (Phase 1 demo) and Lu (Phase 2 production with PVC) lives in [`agent_system_prompt.md`](agent_system_prompt.md) and is signed off by Magalu Legal + Brand + CX before any production traffic. Tool calls (order lookup, delivery status, return initiation, escalation) are HTTPS endpoints into Magalu's existing CX stack; the agent orchestrates and Magalu's services remain source of truth.

The **narration-before-action** pattern (the agent saying what it is about to do before doing it, "pode ser?" before sensitive actions) is enforced by the system prompt across both phases. This is the defensible PII-handling behavior that distinguishes Lu from a generic assistant.

**Deployment risk this component owns:** Hallucination on retail or policy topics (Phase 1 templates and Phase 2 conversational) and escalation failure (Phase 2 conversational surface). See risks #4 and #6.

### Text-to-speech (PT-BR voices via ElevenLabs)

ElevenLabs TTS with model selection per notification template or per conversational turn: `eleven_multilingual_v2` as the primary for warmth and stability on product-name, price, and order-number readback, `eleven_flash_v2_5` held in reserve for short proactive notifications under 8 seconds and high-traffic Phase 2 conversational turns where time-to-first-audio matters more than expressive range.

Voice persona selection:
- **Luiza (warm_female_br, Rachel premade)** in Phase 1, as the prototype voice for all outbound notification templates and the demo voice for stakeholder reviews. Luiza is not Lu; the naming is deliberate.
- **Production Lu = Phase 2 PVC** of Marianna Armellini (or contracted alternative if licensing does not align), with talent licensing handled in parallel by Magalu's legal and talent teams. Production Lu replaces Luiza on every customer-facing notification template at the Phase 2 cutover.
- **Rafael (neutral_male_br)** is reserved for surgical use on high-stakes clarity-leading moments inside the demo surface (order-issue confirmations, payment-related readbacks). Never the production Lu voice.
- **Marina (energetic_female_br)** is pre-selected for celebratory cells in Phase 2 A/B testing (order shipped, Magalu Ouro reward earned). Out of scope for Phase 1.

The model version is pinned in `src/config.py` and in Magalu's deployment config; upgrades go through a 2-week A/B before promotion.

**Deployment risk this component owns:** Voice quality drift across model updates, plus brand-voice impersonation and dilution risk on the production PVC. See risks #1 and #11.

### Knowledge base (RAG over Magalu product catalog, policies, FAQ)

A version-controlled RAG corpus of Magalu's product catalog metadata, return and exchange policy, delivery SLAs, FAQ content, and approved promotional copy. The agent is read-only against this corpus and cites or paraphrases approved language; it does not generate new policy or product claims. The corpus is owned by Magalu CX Content with versioned daily refresh on catalog data (price, stock, availability) and weekly refresh on policy. A CI check flags drift between the corpus and the live catalog and policy systems. This is the surface area where staleness becomes a customer-trust problem and, on price or availability claims, a CDC exposure.

**Deployment risk this component owns:** Training data staleness on retail data. See risk #10.

### CX stack integration (Magalu's CRM, orders, catalog, marketplace systems)

Real-time read of the authenticated customer's profile, current order state, delivery status, return history, and contact history from Magalu's CX stack. Write of conversation summary and outcome at notification or session close. The voice surface never writes customer-facing fields; it writes a structured `ai_conversation_log` record that the human agent reads on escalation, and a notification-outcome record (delivered / listened / replied / converted) for the A/B framework. This is the seam where PII discipline matters most: field-level allowlist on what the agent can read, structured-only output on what it writes.

The marketplace integration (Phase 3+ for seller onboarding voice tutorials) is out of scope for Phase 1 but lives on the same architecture; the marketplace systems are read-only sources for product information and seller metadata.

**Deployment risk this component owns:** PII leakage through CX stack writes or logs, plus marketplace seller voice fraud risk on the seller integration path. See risks #3 and #12.

### Human handoff queue (warm transfer with full context)

The crucial seam, primarily exercised in Phase 2+ on the conversational replying-Lu surface. When the bot escalates, the conversation, transcript, and an AI-generated summary land in Magalu CX Ops' human queue with a named agent assigned. The human picks up with full context, and the customer never has to repeat themselves. The agent does not negotiate with the customer about whether to escalate; customer-initiated escalation is honored on first request. The "Camila" pattern in [`data/support_scripts.json`](../data/support_scripts.json) (`escalation_01`) is the reference exchange.

In Phase 1 (outbound notification only), the handoff seam shows up as a reply path on outbound voice notes: a customer who replies to a notification with intent to escalate is routed into Magalu CX Ops' existing human queue with the notification context attached. There is no autonomous bot resolution on inbound replies during Phase 1.

**Deployment risk this component owns:** Escalation failure (loops, no context, defensive bot behavior). See risk #6.

### Observability and logging layer

Every notification and every Phase 2+ conversational turn is logged with intent confidence (where applicable), tool calls invoked, per-step latency, audio quality flags, A/B cell assignment, downstream conversion outcome, and the redacted transcript. This is the substrate that powers the success metrics in playbook Section 7. Redaction relies on a field-level allowlist enforced before persistence. Retention is LGPD-compliant: 30 days hot, 90 days cold, then deletion, with no transcript export without DPO sign-off.

**Deployment risk this component owns:** PII leakage at the logging layer, and the metric-blindness risk if observability is incomplete. See risk #3.

## What is intentionally not in this architecture (Phase 1)

- **No production voice clone in Phase 1.** Pilot uses ElevenLabs premade Luiza on `eleven_multilingual_v2`. Phase 2 moves to a Professional Voice Clone of approved Brazilian voice talent (Marianna Armellini if licensing aligns, contracted alternative if not). PVC, not Instant Voice Clone; the playbook explains why the distinction is load-bearing. No Magalu production deployment ships on IVC.
- **No conversational replying-Lu surface in Phase 1.** Phase 1 is outbound notification-led. Inbound voice notes are accepted and routed but not autonomously resolved. Conversational replying-Lu ships in Phase 2 with the production PVC.
- **No in-store, web, kiosk, or Magalu Radio surface.** Phase 1 is WhatsApp da Lu only. Magalu App in Phase 2. Physical-store kiosks, owned media, and marketplace seller onboarding are Phase 3.
- **No Magalu Pay scope.** Magalu Pay financial-literacy voice is Phase 4 only, under separate guardrails. Any inbound utterance classified as Magalu Pay scope in Phase 1 or 2 is routed to a human path.
- **No B2B reseller integration.** Magalu Cloud as ElevenLabs reseller for partner retailers is Phase 4.

Naming the absences keeps the Phase 1 architecture clearly bounded.
