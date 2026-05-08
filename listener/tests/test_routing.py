"""Tests for repo full_name → cell lookup."""

from __future__ import annotations

from listener.config import ListenerConfig
from listener.routing import cell_for_repo


def test_known_repo_returns_cell(config: ListenerConfig) -> None:
    cell = cell_for_repo(config, "JSBaxter/atlas")
    assert cell is not None
    assert cell.name == "atlas"


def test_unknown_repo_returns_none(config: ListenerConfig) -> None:
    assert cell_for_repo(config, "JSBaxter/unknown") is None


def test_owner_ignored_only_repo_name_matters(config: ListenerConfig) -> None:
    # Routing keys on the trailing segment; the owner is ignored.
    cell = cell_for_repo(config, "different-owner/atlas")
    assert cell is not None
    assert cell.name == "atlas"
