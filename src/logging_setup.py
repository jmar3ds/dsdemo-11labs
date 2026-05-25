"""Structured per-turn JSON logger with PII redaction at the write layer.

`get_logger` returns a `logging.Logger` configured to write JSONL records to
`outputs/eleven-agents_demo/events.jsonl`. `redact_pii` masks common Brazilian customer identifiers
at the write boundary (CPF, CNPJ, phone numbers, email addresses, and long digit runs)
on a copy of the input, and truncates `agent_response` payloads over 200 chars.
`log_turn` is the per-turn write helper used by the orchestrator.
"""

from __future__ import annotations

import json
import logging
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from src.config import REPO_ROOT

_DEFAULT_EVENTS_LOG_PATH: Path = (
    REPO_ROOT / "outputs" / "eleven-agents_demo" / "events.jsonl"
)
EVENTS_LOG_PATH: Path = _DEFAULT_EVENTS_LOG_PATH

# Common PII patterns seen in Brazilian retail support transcripts.
# Order IDs are intentionally masked too: they are operational identifiers.
_EMAIL_RE: re.Pattern[str] = re.compile(
    r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
)
_CPF_RE: re.Pattern[str] = re.compile(r"\b\d{3}[.\s-]?\d{3}[.\s-]?\d{3}[-\s]?\d{2}\b")
_CNPJ_RE: re.Pattern[str] = re.compile(
    r"\b\d{2}[.\s-]?\d{3}[.\s-]?\d{3}[/\s-]?\d{4}[-\s]?\d{2}\b"
)
_PHONE_RE: re.Pattern[str] = re.compile(
    r"(?<!\d)(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?9?\d{4}[-\s]?\d{4}(?!\d)"
)
_DIGITS_RE: re.Pattern[str] = re.compile(r"\d{4,}")

_AGENT_RESPONSE_MAX: int = 200

_LOGGER: logging.Logger | None = None


class _JsonLineFormatter(logging.Formatter):
    """Emit each LogRecord as a single-line JSON document on `record.msg`."""

    def format(self, record: logging.LogRecord) -> str:
        if isinstance(record.msg, dict):
            return json.dumps(record.msg, ensure_ascii=False, sort_keys=True)
        return json.dumps({"message": record.getMessage()}, ensure_ascii=False)


def _keep_last4_mask(label: str, raw: str) -> str:
    """Return a stable redaction marker that keeps only the final four digits."""
    digits = re.sub(r"\D", "", raw)
    tail = digits[-4:] if len(digits) >= 4 else "****"
    return f"[{label}:***{tail}]"


def _mask_pii(text: str) -> str:
    """Mask CPF, CNPJ, phones, emails, and long digit runs in a string."""
    placeholders: dict[str, str] = {}

    def _stash(value: str) -> str:
        token = f"__PII_{chr(65 + len(placeholders))}__"
        placeholders[token] = value
        return token

    masked = _EMAIL_RE.sub(lambda _: _stash("[email:redacted]"), text)
    masked = _CNPJ_RE.sub(
        lambda m: _stash(_keep_last4_mask("cnpj", m.group(0))), masked
    )
    masked = _CPF_RE.sub(lambda m: _stash(_keep_last4_mask("cpf", m.group(0))), masked)
    masked = _PHONE_RE.sub(
        lambda m: _stash(_keep_last4_mask("phone", m.group(0))), masked
    )

    def _sub_digit_run(match: re.Match[str]) -> str:
        run = match.group(0)
        return "***" + run[-4:]

    masked = _DIGITS_RE.sub(_sub_digit_run, masked)
    for token, value in placeholders.items():
        masked = masked.replace(token, value)
    return masked


def _redact_value(value: object) -> object:
    """Mask PII in strings; recurse into dicts and lists; leave other types alone."""
    if isinstance(value, str):
        return _mask_pii(value)
    if isinstance(value, dict):
        return {k: _redact_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    return value


def redact_pii(record: dict) -> dict:
    """Return a redacted copy of `record`: mask customer identifiers, truncate long responses."""
    redacted = deepcopy(record)

    # Top-level pass: mask digit runs in every string value (and nested structures).
    for key, value in list(redacted.items()):
        redacted[key] = _redact_value(value)

    # Truncate agent_response after redaction so the truncation marker is preserved.
    response = redacted.get("agent_response")
    if isinstance(response, str) and len(response) > _AGENT_RESPONSE_MAX:
        redacted["agent_response"] = response[:_AGENT_RESPONSE_MAX] + "[truncated]"

    return redacted


def _ensure_log_path() -> Path:
    """Create the events.jsonl parent directory if missing and return the file path."""
    EVENTS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    return EVENTS_LOG_PATH


def set_log_path(path: Path | None) -> Path:
    """Override the events.jsonl path for tests. Pass `None` to restore the default.

    Resets the cached logger so the next `get_logger()` call rebinds its FileHandler
    to the new path. Returns the active path after the override.
    """
    global EVENTS_LOG_PATH, _LOGGER
    EVENTS_LOG_PATH = Path(path) if path is not None else _DEFAULT_EVENTS_LOG_PATH
    if _LOGGER is not None:
        for handler in list(_LOGGER.handlers):
            handler.close()
            _LOGGER.removeHandler(handler)
        _LOGGER = None
    return EVENTS_LOG_PATH


def get_logger(name: str = "dsdemo_11labs.eleven-agents") -> logging.Logger:
    """Return a JSON-line logger that writes to `outputs/eleven-agents_demo/events.jsonl`."""
    global _LOGGER
    if _LOGGER is not None and _LOGGER.name == name:
        return _LOGGER

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    path = _ensure_log_path()
    if not any(
        isinstance(h, logging.FileHandler)
        and getattr(h, "baseFilename", "") == str(path)
        for h in logger.handlers
    ):
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(_JsonLineFormatter())
        logger.addHandler(handler)

    _LOGGER = logger
    return logger


def log_turn(record: dict) -> None:
    """Apply PII redaction and write `record` as one JSON line to events.jsonl."""
    payload = redact_pii(record)
    payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    logger = get_logger()
    logger.info(payload)
