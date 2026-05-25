"""Central configuration for dsdemo-11labs.

Loads the ElevenLabs API key from .env, defines repo paths, reads the
voice catalog and support scripts. Every other module should import from
here rather than re-reading the JSON files or re-parsing .env.

Design notes:
- Paths are resolved relative to the repo root (the parent of src/), not
  the current working directory. This way the CLIs work regardless of
  where the user runs them from.
- Voice catalog and support scripts are loaded lazily so the modules can
  be imported even if data files are temporarily missing (useful for
  --help output and unit tests).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# src/config.py -> src/ -> repo root
REPO_ROOT: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path = REPO_ROOT / "data"
OUTPUTS_DIR: Path = REPO_ROOT / "outputs"
SAMPLES_DIR: Path = REPO_ROOT / "samples"

VOICE_CATALOG_PATH: Path = DATA_DIR / "voice_catalog.json"
SUPPORT_SCRIPTS_PATH: Path = DATA_DIR / "support_scripts.json"

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

# Load .env from the repo root (not the cwd) so the CLIs work from anywhere.
load_dotenv(dotenv_path=REPO_ROOT / ".env")

API_KEY: Optional[str] = os.environ.get("ELEVENLABS_API_KEY")

# Recommended PT-BR model : verified against elevenlabs-python >= 1.0.0
# eleven_multilingual_v2 is the current best general-purpose multilingual TTS
# model. For latency-sensitive use cases (conversational), see eleven_flash_v2_5.
DEFAULT_MODEL_ID: str = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

# mp3_44100_128 is the standard high-quality format for samples / web playback.
# For telephony, use ulaw_8000.
DEFAULT_OUTPUT_FORMAT: str = "mp3_44100_128"

# Default voice : must exist in voice_catalog.json under "name"
DEFAULT_VOICE_NAME: str = os.environ.get("DEFAULT_VOICE", "warm_female_br")

# ---------------------------------------------------------------------------
# Domain objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Voice:
    """A single entry in the voice catalog."""

    name: str
    display_name: str
    voice_id: str
    description: str
    rationale: str
    tradeoffs: str

    @classmethod
    def from_dict(cls, d: dict) -> "Voice":
        return cls(
            name=d["name"],
            display_name=d.get("display_name", d["name"]),
            voice_id=d["voice_id"],
            description=d.get("description", ""),
            rationale=d.get("rationale", ""),
            tradeoffs=d.get("tradeoffs", ""),
        )


@dataclass(frozen=True)
class Script:
    """A single entry in support_scripts.json."""

    id: str
    use_case: str
    language: str
    agent_line: str
    context: str
    expected_voice: str

    @classmethod
    def from_dict(cls, d: dict) -> "Script":
        return cls(
            id=d["id"],
            use_case=d.get("use_case", ""),
            language=d.get("language", "pt-BR"),
            agent_line=d["agent_line"],
            context=d.get("context", ""),
            expected_voice=d.get("expected_voice", DEFAULT_VOICE_NAME),
        )


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_voice_catalog() -> dict[str, Voice]:
    """Read voice_catalog.json. Returns a {name: Voice} mapping.

    Raises FileNotFoundError or ValueError with a clear message if the file
    is missing or malformed.
    """
    if not VOICE_CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"Voice catalog not found at {VOICE_CATALOG_PATH}. "
            "Did you delete data/voice_catalog.json?"
        )
    try:
        with VOICE_CATALOG_PATH.open(encoding="utf-8") as fh:
            payload = json.load(fh)
    except json.JSONDecodeError as e:
        raise ValueError(f"voice_catalog.json is not valid JSON: {e}") from e

    voices_raw = payload.get("voices", [])
    if not voices_raw:
        raise ValueError("voice_catalog.json has no 'voices' array.")

    return {entry["name"]: Voice.from_dict(entry) for entry in voices_raw}


def load_support_scripts() -> list[Script]:
    """Read support_scripts.json. Returns a list of Script objects in file order."""
    if not SUPPORT_SCRIPTS_PATH.exists():
        raise FileNotFoundError(
            f"Support scripts not found at {SUPPORT_SCRIPTS_PATH}. "
            "Did you delete data/support_scripts.json?"
        )
    try:
        with SUPPORT_SCRIPTS_PATH.open(encoding="utf-8") as fh:
            payload = json.load(fh)
    except json.JSONDecodeError as e:
        raise ValueError(f"support_scripts.json is not valid JSON: {e}") from e

    scripts_raw = payload.get("scripts", [])
    if not scripts_raw:
        raise ValueError("support_scripts.json has no 'scripts' array.")

    return [Script.from_dict(entry) for entry in scripts_raw]


def get_voice(name: str) -> Voice:
    """Look up a voice by its catalog name. Raises ValueError with a helpful list if missing."""
    catalog = load_voice_catalog()
    if name not in catalog:
        available = ", ".join(sorted(catalog.keys()))
        raise ValueError(
            f"Voice '{name}' not found in catalog. Available voices: {available}"
        )
    return catalog[name]


def ensure_outputs_dir() -> Path:
    """Make sure outputs/ exists and return its path."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUTS_DIR
