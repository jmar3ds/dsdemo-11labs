"""generate_voice.py : single-shot text -> mp3 CLI.

Usage:
    python -m src.generate_voice --text "Olá, tudo bem?" --voice warm_female_br
    python -m src.generate_voice --text-file scripts/welcome.txt --output outputs/welcome.mp3

Reads the API key from .env (see .env.example). Writes an mp3 to outputs/
(or to the path you pass to --output) and prints a summary line.

Error policy:
    Every expected failure mode (missing key, invalid voice, network issue,
    API error) prints exactly one human-readable line and exits non-zero.
    No stack traces in normal operation. Unexpected failures still raise
    so they don't get silently swallowed.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

import click

from . import config
from .console import console, error, info, success

# ---------------------------------------------------------------------------
# ElevenLabs SDK import : guarded so --help works even if the SDK is missing
# ---------------------------------------------------------------------------

# VERIFY: confirm current API shape
# Verified against elevenlabs-python (Context7 docs, 2026-05-16):
#   from elevenlabs import ElevenLabs
#   client = ElevenLabs(api_key=...)
#   audio = client.text_to_speech.convert(
#       text=..., voice_id=..., model_id=..., output_format="mp3_44100_128"
#   )
# The returned `audio` is an iterator/bytes-like stream of mp3 chunks.

try:
    from elevenlabs import ElevenLabs  # type: ignore
    from elevenlabs.core.api_error import ApiError  # type: ignore
    _SDK_AVAILABLE = True
    _SDK_IMPORT_ERROR: Optional[Exception] = None
except Exception as e:  # pragma: no cover : only triggered when SDK is missing
    ElevenLabs = None  # type: ignore
    ApiError = Exception  # type: ignore : fallback so except clauses don't break
    _SDK_AVAILABLE = False
    _SDK_IMPORT_ERROR = e


# ---------------------------------------------------------------------------
# Core synthesis function : kept separate so other scripts can reuse it
# ---------------------------------------------------------------------------


def synthesize(
    text: str,
    voice_name: str,
    model_id: str,
    output_path: Path,
) -> dict:
    """Synthesize one mp3. Returns a summary dict; raises on failure.

    Returns:
        {
          "output_path": Path,
          "voice_name": str,
          "voice_display_name": str,
          "voice_id": str,
          "model_id": str,
          "characters": int,
          "duration_seconds": float,   # wall-clock, not audio length
          "bytes_written": int,
        }
    """
    if not _SDK_AVAILABLE:
        raise RuntimeError(
            "elevenlabs SDK is not installed. Run: pip install -r requirements.txt"
        )
    if not config.API_KEY:
        raise RuntimeError(
            "ELEVENLABS_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    voice = config.get_voice(voice_name)  # raises ValueError with helpful message

    client = ElevenLabs(api_key=config.API_KEY)

    started = time.monotonic()
    audio_iter = client.text_to_speech.convert(
        text=text,
        voice_id=voice.voice_id,
        model_id=model_id,
        output_format=config.DEFAULT_OUTPUT_FORMAT,
    )

    # The SDK returns an iterator of bytes chunks. Stream to disk so we don't
    # hold the entire mp3 in memory (matters for long batch runs).
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bytes_written = 0
    with output_path.open("wb") as fh:
        for chunk in audio_iter:
            if chunk:
                fh.write(chunk)
                bytes_written += len(chunk)
    duration = time.monotonic() - started

    return {
        "output_path": output_path,
        "voice_name": voice.name,
        "voice_display_name": voice.display_name,
        "voice_id": voice.voice_id,
        "model_id": model_id,
        "characters": len(text),
        "duration_seconds": round(duration, 2),
        "bytes_written": bytes_written,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _read_text_source(text: Optional[str], text_file: Optional[Path]) -> str:
    """Resolve --text vs --text-file. Exactly one must be provided."""
    if text and text_file:
        raise click.UsageError("Pass either --text or --text-file, not both.")
    if not text and not text_file:
        raise click.UsageError("You must pass either --text or --text-file.")
    if text_file:
        if not text_file.exists():
            raise click.UsageError(f"Text file not found: {text_file}")
        return text_file.read_text(encoding="utf-8").strip()
    assert text is not None  # for type checkers
    return text


def _default_output_path() -> Path:
    """outputs/<timestamp>.mp3"""
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return config.ensure_outputs_dir() / f"{stamp}.mp3"


@click.command()
@click.option("--text", type=str, default=None, help="PT-BR text to synthesize.")
@click.option(
    "--text-file",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to a .txt file containing the text to synthesize.",
)
@click.option(
    "--voice",
    "voice_name",
    type=str,
    default=config.DEFAULT_VOICE_NAME,
    show_default=True,
    help="Voice name from data/voice_catalog.json.",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path for the generated mp3. Defaults to outputs/<timestamp>.mp3.",
)
@click.option(
    "--model",
    "model_id",
    type=str,
    default=config.DEFAULT_MODEL_ID,
    show_default=True,
    help="ElevenLabs model id. Recommended for PT-BR: eleven_multilingual_v2.",
)
def main(
    text: Optional[str],
    text_file: Optional[Path],
    voice_name: str,
    output_path: Optional[Path],
    model_id: str,
) -> None:
    """Generate a single PT-BR mp3 from text using ElevenLabs TTS."""
    try:
        resolved_text = _read_text_source(text, text_file)
        resolved_output = output_path or _default_output_path()
        summary = synthesize(
            text=resolved_text,
            voice_name=voice_name,
            model_id=model_id,
            output_path=resolved_output,
        )
    except click.UsageError:
        raise  # let click format usage errors
    except FileNotFoundError as e:
        error(str(e))
        sys.exit(2)
    except ValueError as e:
        # Invalid voice, malformed catalog, etc : already has a friendly message.
        error(str(e))
        sys.exit(2)
    except RuntimeError as e:
        # SDK missing or API key missing : already has a friendly message.
        error(str(e))
        sys.exit(2)
    except ApiError as e:  # type: ignore[misc]
        # ElevenLabs returned an error (auth, quota, invalid voice_id, etc).
        status = getattr(e, "status_code", "?")
        body = getattr(e, "body", str(e))
        error(f"ElevenLabs API error (HTTP {status}): {body}")
        sys.exit(3)
    except (ConnectionError, TimeoutError, OSError) as e:
        # Network-level failure. OSError covers DNS, broken pipe, etc.
        error(f"Network error talking to ElevenLabs: {e}")
        sys.exit(4)

    success(f"Generated: {summary['output_path']}")
    info(
        f"  voice: {summary['voice_display_name']} ({summary['voice_name']}) "
        f"| voice_id: {summary['voice_id']}"
    )
    info(
        f"  model: {summary['model_id']} | chars: {summary['characters']} "
        f"| bytes: {summary['bytes_written']} | wall: {summary['duration_seconds']}s"
    )


if __name__ == "__main__":
    main()
