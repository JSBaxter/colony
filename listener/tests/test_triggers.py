"""Tests for per-cell mutex serialization + audit log writing."""

from __future__ import annotations

import asyncio
import json

import pytest

from listener.config import ListenerConfig
from listener.triggers import handle_merge


@pytest.mark.asyncio
async def test_audit_log_written(config: ListenerConfig) -> None:
    cell = config.cells["atlas"]
    await handle_merge(
        config=config,
        cell=cell,
        pr_number=7,
        merge_sha="abc123",
        pr_title="t",
        pr_author="bot",
    )
    lines = config.audit_log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["kind"] == "pr_merged"
    assert record["cell"] == "atlas"
    assert record["pr_number"] == 7
    assert record["merge_sha"] == "abc123"
    assert "ts" in record


@pytest.mark.asyncio
async def test_same_cell_triggers_serialize(config: ListenerConfig) -> None:
    """Two concurrent triggers on the same cell both record without races."""
    cell = config.cells["atlas"]
    await asyncio.gather(
        handle_merge(config, cell, 1, "a", "p1", "u"),
        handle_merge(config, cell, 2, "b", "p2", "u"),
    )
    lines = config.audit_log_path.read_text().strip().splitlines()
    assert len(lines) == 2
    pr_numbers = sorted(json.loads(line)["pr_number"] for line in lines)
    assert pr_numbers == [1, 2]


@pytest.mark.asyncio
async def test_different_cells_can_parallelize(config: ListenerConfig) -> None:
    """Different cells get different locks; both events recorded."""
    atlas = config.cells["atlas"]
    cytometer = config.cells["cytometer"]
    await asyncio.gather(
        handle_merge(config, atlas, 1, "a", "p1", "u"),
        handle_merge(config, cytometer, 2, "b", "p2", "u"),
    )
    lines = config.audit_log_path.read_text().strip().splitlines()
    assert len(lines) == 2
    cells = sorted(json.loads(line)["cell"] for line in lines)
    assert cells == ["atlas", "cytometer"]
