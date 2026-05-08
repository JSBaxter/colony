"""Per-cell trigger handler.

Same-cell triggers serialize via an asyncio.Lock; cross-cell triggers run
in parallel. Each trigger appends to the audit JSONL log and prints a
human-readable line (with terminal bell) to stdout.
"""

from __future__ import annotations

import asyncio
import sys
from collections import defaultdict
from typing import Any

from listener.audit import append as audit_append
from listener.config import CellConfig, ListenerConfig

# One lock per cell name. defaultdict creates new locks on first access.
_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


async def handle_merge(
    config: ListenerConfig,
    cell: CellConfig,
    pr_number: int,
    merge_sha: str | None,
    pr_title: str,
    pr_author: str,
) -> None:
    """Record a PR-merge trigger event for `cell`. Serialized per-cell."""
    async with _locks[cell.name]:
        event: dict[str, Any] = {
            "kind": "pr_merged",
            "cell": cell.name,
            "cell_path": str(cell.path),
            "pr_number": pr_number,
            "merge_sha": merge_sha,
            "pr_title": pr_title,
            "pr_author": pr_author,
        }
        audit_append(config.audit_log_path, event)
        sys.stdout.write(
            f"\a[trigger] {cell.name} ← merged PR #{pr_number} ({pr_title})\n"
        )
        sys.stdout.flush()
