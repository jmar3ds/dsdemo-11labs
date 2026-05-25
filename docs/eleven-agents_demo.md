# ElevenAgents Demo: how to run

This ElevenAgents deliverable is a live voice exchange between a microphone, an
ElevenAgents agent (the customer-facing "Lu"), and a Python
orchestrator that routes each turn through three Magalu client tools backed
by a local FastAPI mock. This page is the operator's runbook.

## 1. Install dependencies

From the repo root (`dsdemo-11labs/`):

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For the live demo, also install PortAudio (the system library that backs
PyAudio's mic + speaker streams). On macOS:

```
brew install portaudio
pip install pyaudio
```

On Debian/Ubuntu:

```
sudo apt install portaudio19-dev
pip install pyaudio
```

PyAudio is only needed to drive the actual microphone. Tests and
import-time verification work without it.

## 2. Configure `.env`

Copy `.env.example` to `.env` and set:

```
ELEVENLABS_API_KEY=sk_...        # account API key with ElevenAgents scope
ELEVENLABS_AGENT_ID=agent_...    # the dashboard agent id (Lu)
```

The agent must be configured in the ElevenLabs dashboard with three client
tools declared by name: `lookup_order`, `lookup_delivery_eta`, `lookup_cart`.
The Python runner provides the implementations; the dashboard owns the
prompt, voice, and tool schema.

## 3. Start the mock backend

The orchestrator's tool layer calls a local FastAPI service that returns
fixture orders, ETAs, and carts. In one terminal:

```
make mock
```

This starts `http://127.0.0.1:8000`. A health probe is at `/health`.

## 4. Start the demo

In a second terminal:

```
make demo
```

`make demo` first runs `demo_prereqs` (a curl against the mock backend) so
you get a clean error if the mock is not up. Then it launches
`python3 -m src.run_demo`, which:

1. Loads the agent id and API key from `.env`.
2. Constructs three async tool bridges that adapt the agent's dashboard tools
   to our `tools.py` async layer.
3. Opens an authenticated WebSocket to the agent and starts streaming audio
   from the default microphone via `DefaultAudioInterface`.
4. Logs every transcript, agent response, latency measurement, and tool
   invocation to `outputs/eleven-agents_demo/events.jsonl`.

Speak after the session opens. Ctrl+C ends the call cleanly (the runner
installs a SIGINT handler that calls `Conversation.end_session`).

## 5. Read the output

`outputs/eleven-agents_demo/events.jsonl` is the canonical artifact. Each line is one
event with a UTC timestamp. Notable event names:

- `session_start`, `session_end`: the runner boundaries.
- `eleven-agents_user_transcript`, `eleven-agents_agent_response`: what the customer said
  and what the agent said, sourced from the SDK callbacks.
- `eleven-agents_latency_measurement`: ElevenAgents round-trip latency reported by the
  server, in ms.
- `tool_bridge_called`, `tool_bridge_returned`: each agent-invoked tool
  call, with `latency_ms` for the call itself.
- `turn_start`, `classified`, `narration_emitted`, `tool_called`,
  `tool_returned`, `agent_response`, `turn_complete`, `escalated`: emitted
  by the local orchestrator pipeline (Steps 1 to 4), used when the
  orchestrator drives a scripted turn end-to-end without the cloud agent.

PII redaction is applied at the write layer: formatted CPF, CNPJ, phone numbers,
email addresses, and long digit runs are masked before they reach the JSONL log.
Order numbers in transcripts and tool arguments are therefore safe to share in
review artifacts.

## 6. Known limitations of the prototype

- The runner is a single-process Python program. No reconnect-on-drop logic
  beyond what the SDK provides; if the network blips, you hang up and
  restart.
- The mock backend's order corpus is five fixtures (`data/mock_orders.json`).
  Asking the agent for an order id not in that file surfaces a 404 through
  the tool bridge, which the agent should narrate as a polite "I couldn't
  find that order" using its dashboard prompt.
- `lookup_cart` uses whatever `customer_id` the agent passes. In a real
  deployment this would come from the session metadata (phone number to
  customer id lookup); here, the demo agent prompt hardcodes `cust-demo`.
- The orchestrator's structured turn pipeline (`handle_turn`) is exercised
  by the unit tests under `tests/`. The cloud-agent runner does not invoke
  `handle_turn` directly because the dashboard agent owns the intent
  classification and response phrasing. The local pipeline and the cloud
  runner share the tools layer and the structured logger, which is what
  makes the timeline in `events.jsonl` coherent across both modes.

## 7. Troubleshooting

- `[run_demo] configuration error: ELEVENLABS_AGENT_ID missing from .env`:
  set the agent id in `.env`.
- `Mock backend not running.`: run `make mock` in another terminal first.
- `ModuleNotFoundError: pyaudio`: install PortAudio + PyAudio (see Section 1).
  Import-time verification (`python -c "from src.run_demo import main"`)
  does not require PyAudio because the audio interface is built lazily
  inside `build_session`.
