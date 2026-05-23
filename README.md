# Fale com a Lu da Magalu

**Voice AI for Brazilian retail operations. A deployment-strategy prototype centered on Magazine Luiza's WhatsApp da Lu surface.**

## What this is

This repo is the proof-of-work artifact for João Marcos' ElevenLabs Deployment Strategist application. It combines a PT-BR voice prototype, a local Python orchestration layer, mock Magalu tools, tests, a risk register, and a consulting-style deployment playbook.

The customer scenario is built from public information and treated as a working hypothesis, not as a signed Magalu engagement.

## 3-minute reviewer path

1. Access the website https://joaomarcos-dsworksample-11labs.click/ to view the case-study page.
2. Listen to `../samples/greeting.mp3`, `../samples/delivery-eta.mp3`, and `../samples/human-handoff.mp3` if you do not want to grant mic access to the live widget.
3. Skim `docs/deployment_playbook.md`, especially sections 1, 7, 11, and 12.
4. Run `python -m pytest tests/ -q` to verify the local orchestration tests.

## What this proves

- Customer workflow discovery for a real Brazilian enterprise surface.
- PT-BR voice/audio judgment and production-quality sample curation.
- Deployment risk thinking: PII boundaries, handoff design, talent licensing, rollout gates.
- Python/API prototyping with tests, retry behavior, structured logs, and mock backend tools.
- Commercial framing for an enterprise AI deployment.

## Why Magalu

Magalu has a large Brazilian customer base, a well-known virtual brand persona in Lu, and a WhatsApp commerce surface where customers already send voice notes. The gap this prototype explores is one-directional voice: customers speak, but Lu replies primarily in text.

## Repo tour

| Folder / file | What's in it |
|---|---|
| `docs/deployment_playbook.md` | Headline consulting artifact: context, discovery questions, rollout phases, success gates, risk, and commercial structures. |
| `docs/architecture.md` | Reference architecture with deployment-risk ownership. |
| `docs/agent_system_prompt.md` | Production-style system prompt for the Luiza agent: identity, tone, PII rules, escalation triggers, sample dialogues. |
| `docs/quality_rubric.md` | PT-BR voice evaluation scorecard. |
| `docs/risk_register.md` | Top deployment risks with likelihood, impact, owner, and mitigation. |
| `src/` | Python CLI tools plus the local turn orchestrator. |
| `mock_backend/` | FastAPI fixture service for order status, delivery ETA, and cart data. |
| `tests/` | Pytest suite covering intent routing, narration-before-action, retry behavior, PII redaction, and dynamic tool responses. |
| `data/voice_catalog.json` | Luiza, Rafael, and Marina prototype voices with rationale and tradeoffs. |
| `samples/` | Curated MP3 fallback samples for reviewers. |

## How to run locally

```bash
# 1. Clone and enter
git clone https://github.com/jmar3ds/dsdemo-11labs.git
cd dsdemo-11labs

# 2. Install dependencies (Python 3.11+)
pip install -r requirements.txt

# 3. Run tests
python -m pytest tests/ -q

# 4. Optional: start the mock backend
make mock

# 5. Optional: run the ElevenAgents live demo after configuring .env
cp .env.example .env
# edit .env with ELEVENLABS_API_KEY and ELEVENLABS_AGENT_ID
make demo
```

Each script supports `--help` for full CLI options.

## Public page vs local repo

The public case-study page embeds an ElevenAgents widget. This repo does not recreate the cloud agent without an ElevenLabs API key and agent ID. The local repo proves the deployable parts that can be reviewed offline: Python tool bridges, mock services, tests, PII-redacted logs, curated audio samples, and the deployment playbook.

## Limitations and honesty

- No real WhatsApp Business API or Magalu integration is included. The architecture is reference-level; production wiring belongs in a real engagement.
- No persistent voice clone is included. Phase 1 uses a premade bridge voice. Production Lu requires licensed talent and a Professional Voice Clone (PVC).
- The mock backend uses fixture data only. It is designed to make the deployment pattern reviewable, not to simulate Magalu's real systems.
- Public information about Magalu is cited in the playbook where relevant. The commercial proposal is a hypothesis, not a claim of insider knowledge.

## Contact

- LinkedIn: [linkedin.com/in/joaomarcosds](https://www.linkedin.com/in/joaomarcosds)
