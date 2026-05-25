"""Tiny console helper with graceful rich -> plain-print fallback.

Why this exists:
    The spec requires `rich` for nice output but graceful fallback to plain
    print if rich is unavailable. Centralizing that here means each CLI
    script can just import and use info/success/error/warn without checking
    for rich every time.
"""

from __future__ import annotations

import sys
from typing import Any, Optional

try:
    from rich.console import Console  # type: ignore
    from rich.table import Table  # type: ignore
    _RICH_AVAILABLE = True
    console: Optional["Console"] = Console()
    err_console: Optional["Console"] = Console(stderr=True)
except Exception:  # pragma: no cover
    _RICH_AVAILABLE = False
    console = None
    err_console = None
    Table = None  # type: ignore


def info(msg: str) -> None:
    """Neutral status line, written to stdout."""
    if console is not None:
        console.print(msg, style="dim")
    else:
        print(msg)


def success(msg: str) -> None:
    """Successful outcome, written to stdout."""
    if console is not None:
        console.print(msg, style="bold green")
    else:
        print(f"[OK] {msg}")


def warn(msg: str) -> None:
    """Recoverable issue, written to stderr."""
    if err_console is not None:
        err_console.print(f"warning: {msg}", style="yellow")
    else:
        print(f"warning: {msg}", file=sys.stderr)


def error(msg: str) -> None:
    """Fatal error, written to stderr. The caller is expected to exit non-zero."""
    if err_console is not None:
        err_console.print(f"error: {msg}", style="bold red")
    else:
        print(f"error: {msg}", file=sys.stderr)


def print_table(headers: list[str], rows: list[list[Any]], title: Optional[str] = None) -> None:
    """Render a table with rich if available, plain aligned text otherwise."""
    if console is not None and Table is not None:
        table = Table(title=title, show_lines=False)
        for h in headers:
            table.add_column(h)
        for row in rows:
            table.add_row(*[str(c) for c in row])
        console.print(table)
        return

    # Fallback: plain aligned output.
    if title:
        print(f"\n=== {title} ===")
    widths = [len(h) for h in headers]
    str_rows = [[str(c) for c in row] for row in rows]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    fmt = "  ".join("{:<" + str(w) + "}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in str_rows:
        print(fmt.format(*row))
