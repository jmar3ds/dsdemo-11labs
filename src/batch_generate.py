"""batch_generate.py : generate one mp3 per entry in support_scripts.json.

Usage:
    python -m src.batch_generate
    python -m src.batch_generate --only greeting_01 closing_01
    python -m src.batch_generate --voice warm_female_br  # override per-script voice

Writes to outputs/batch_<timestamp>/ and prints a summary table at the end.
Per-script failures don't kill the batch : they're recorded as 'failed' rows
so a long-running batch finishes and tells you what to fix.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

import click

from . import config
from .console import error, info, print_table, success, warn
from .generate_voice import _SDK_AVAILABLE, ApiError, synthesize  # reuse the core


def _batch_dir() -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return config.ensure_outputs_dir() / f"batch_{stamp}"


@click.command()
@click.option(
    "--only",
    multiple=True,
    help="If provided, only generate these script IDs (repeatable).",
)
@click.option(
    "--voice",
    "voice_override",
    type=str,
    default=None,
    help="Override every script's expected_voice with this voice name.",
)
@click.option(
    "--model",
    "model_id",
    type=str,
    default=config.DEFAULT_MODEL_ID,
    show_default=True,
    help="ElevenLabs model id.",
)
def main(only: tuple[str, ...], voice_override: Optional[str], model_id: str) -> None:
    """Batch-generate all (or selected) Magalu support scripts."""
    if not _SDK_AVAILABLE:
        error("elevenlabs SDK is not installed. Run: pip install -r requirements.txt")
        sys.exit(2)
    if not config.API_KEY:
        error("ELEVENLABS_API_KEY is not set. Copy .env.example to .env and add your key.")
        sys.exit(2)

    try:
        scripts = config.load_support_scripts()
    except (FileNotFoundError, ValueError) as e:
        error(str(e))
        sys.exit(2)

    if only:
        wanted = set(only)
        scripts = [s for s in scripts if s.id in wanted]
        missing = wanted - {s.id for s in scripts}
        for m in sorted(missing):
            warn(f"Script id '{m}' not found : skipping.")
        if not scripts:
            error("No scripts matched --only. Nothing to do.")
            sys.exit(2)

    out_dir = _batch_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    info(f"Batch output directory: {out_dir}")
    info(f"Generating {len(scripts)} script(s) with model {model_id}...")

    rows: list[list[str]] = []
    total_chars = 0
    for script in scripts:
        voice_to_use = voice_override or script.expected_voice
        out_path = out_dir / f"{script.id}.mp3"
        try:
            summary = synthesize(
                text=script.agent_line,
                voice_name=voice_to_use,
                model_id=model_id,
                output_path=out_path,
            )
            total_chars += summary["characters"]
            rows.append([
                script.id,
                summary["voice_display_name"],
                str(summary["characters"]),
                f"{summary['duration_seconds']}s",
                "ok",
            ])
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            rows.append([script.id, voice_to_use, "-", "-", f"failed: {e}"])
        except ApiError as e:  # type: ignore[misc]
            status = getattr(e, "status_code", "?")
            rows.append([script.id, voice_to_use, "-", "-", f"api error {status}"])
        except (ConnectionError, TimeoutError, OSError) as e:
            rows.append([script.id, voice_to_use, "-", "-", f"network error: {e}"])

    print_table(
        headers=["id", "voice", "chars", "wall", "status"],
        rows=rows,
        title=f"Batch summary ({len(scripts)} scripts, {total_chars} chars total)",
    )

    failures = [r for r in rows if not r[-1].startswith("ok")]
    if failures:
        warn(f"{len(failures)} script(s) failed. See the status column above.")
        sys.exit(1)
    success(f"Batch complete: {out_dir}")


if __name__ == "__main__":
    main()
