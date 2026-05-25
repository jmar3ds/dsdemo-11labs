"""Per-stage latency capture via `time.perf_counter`.

`StageTimer` is a context manager that records the elapsed wall-clock time of
one orchestrator stage (classify, tool call, TTS first-chunk). The captured
elapsed seconds populate the `latency_ms` field on each AgentTurn.
"""

from __future__ import annotations

import time
from types import TracebackType


class StageTimer:
    """Context manager that records wall-clock seconds for one orchestrator stage."""

    def __init__(self, stage: str) -> None:
        self.stage: str = stage
        self.elapsed_seconds: float = 0.0
        self._started: float = 0.0

    def __enter__(self) -> "StageTimer":
        self._started = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.elapsed_seconds = time.perf_counter() - self._started
