"""compare_voices.py : generate the same line in every catalog voice for A/B/C.

Usage:
    python -m src.compare_voices --text "Oi, aqui é a Lu da Magalu."
    python -m src.compare_voices --script-id greeting_01
    python -m src.compare_voices --script-id greeting_01 --label demo_landing

This is the demo used on the landing page so visitors can hear the same script
in the warm, neutral, and energetic profiles back to back. Output:
    outputs/comparison_<timestamp>_<label>/<voice_name>.mp3
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

import click

from . import config
from .console import error, info, print_table, success, warn
from .generate_voice import _SDK_AVAILABLE, ApiError, synthesize


def _comparison_dir(label: Optional[str]) -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    suffix = f"_{label}" if label else ""
    return config.ensure_outputs_dir() / f"comparison_{stamp}{suffix}"


def _resolve_text(text: Optional[str], script_id: Optional[str]) -> tuple[str, str]:
    """Return (text, source_label). Exactly one of --text / --script-id required."""
    if text and script_id:
        raise click.UsageError("Pass either --text or --script-id, not both.")
    if not text and not script_id:
        raise click.UsageError("You must pass either --text or --script-id.")
    if script_id:
        scripts = config.load_support_scripts()
        match = next((s for s in scripts if s.id == script_id), None)
        if match is None:
            available = ", ".join(s.id for s in scripts)
            raise click.UsageError(
                f"Script id '{script_id}' not found. Available: {available}"
            )
        return match.agent_line, f"script:{script_id}"
    assert text is not None
    return text, "text:cli"


@click.command()
@click.option("--text", type=str, default=None, help="PT-BR text to synthesize.")
@click.option(
    "--script-id",
    type=str,
    default=None,
    help="Use the agent_line from this script id in support_scripts.json.",
)
@click.option(
    "--label",
    type=str,
    default=None,
    help="Optional suffix appended to the output dir name (e.g. 'landing_page').",
)
@click.option(
    "--model",
    "model_id",
    type=str,
    default=config.DEFAULT_MODEL_ID,
    show_default=True,
)
def main(
    text: Optional[str],
    script_id: Optional[str],
    label: Optional[str],
    model_id: str,
) -> None:
    """Generate the same line in every voice in the catalog (A/B/C demo)."""
    if not _SDK_AVAILABLE:
        error("elevenlabs SDK is not installed. Run: pip install -r requirements.txt")
        sys.exit(2)
    if not config.API_KEY:
        error("ELEVENLABS_API_KEY is not set. Copy .env.example to .env and add your key.")
        sys.exit(2)

    try:
        resolved_text, source_label = _resolve_text(text, script_id)
        catalog = config.load_voice_catalog()
    except (FileNotFoundError, ValueError) as e:
        error(str(e))
        sys.exit(2)
    except click.UsageError:
        raise

    out_dir = _comparison_dir(label)
    out_dir.mkdir(parents=True, exist_ok=True)
    info(f"Source: {source_label}")
    info(f"Output dir: {out_dir}")
    info(f"Comparing {len(catalog)} voices with model {model_id}...")

    rows: list[list[str]] = []
    for voice_name, voice in catalog.items():
        out_path = out_dir / f"{voice_name}.mp3"
        try:
            summary = synthesize(
                text=resolved_text,
                voice_name=voice_name,
                model_id=model_id,
                output_path=out_path,
            )
            rows.append([
                voice_name,
                summary["voice_display_name"],
                str(summary["characters"]),
                f"{summary['duration_seconds']}s",
                "ok",
            ])
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            rows.append([voice_name, voice.display_name, "-", "-", f"failed: {e}"])
        except ApiError as e:  # type: ignore[misc]
            status = getattr(e, "status_code", "?")
            rows.append([voice_name, voice.display_name, "-", "-", f"api error {status}"])
        except (ConnectionError, TimeoutError, OSError) as e:
            rows.append([voice_name, voice.display_name, "-", "-", f"network: {e}"])

    print_table(
        headers=["voice", "display", "chars", "wall", "status"],
        rows=rows,
        title=f"Voice comparison ({len(catalog)} voices)",
    )

    failures = [r for r in rows if not r[-1].startswith("ok")]
    if failures:
        warn(f"{len(failures)} voice(s) failed. See the status column above.")
        sys.exit(1)
    success(f"Comparison complete: {out_dir}")


if __name__ == "__main__":
    main()
