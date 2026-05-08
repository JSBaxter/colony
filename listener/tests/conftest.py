"""Pytest fixtures shared across the listener test suite."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from listener.app import create_app
from listener.config import CellConfig, ListenerConfig
from listener.triggers import _locks


@pytest.fixture(autouse=True)
def reset_cell_locks() -> Iterator[None]:
    """Clear per-cell asyncio locks between tests so they're isolated."""
    _locks.clear()
    yield
    _locks.clear()


@pytest.fixture
def webhook_secret() -> str:
    return "test-secret-do-not-use-in-prod"


@pytest.fixture
def config(tmp_path: Path, webhook_secret: str) -> ListenerConfig:
    return ListenerConfig(
        cells={
            "atlas": CellConfig(name="atlas", path=tmp_path / "atlas"),
            "cytometer": CellConfig(name="cytometer", path=tmp_path / "cytometer"),
        },
        webhook_secret=webhook_secret,
        audit_log_path=tmp_path / "audit.jsonl",
    )


@pytest.fixture
def client(tmp_path: Path, webhook_secret: str) -> TestClient:
    config_yaml = tmp_path / "config.yml"
    config_yaml.write_text(
        f"""
webhook_secret: {webhook_secret}
audit_log_path: {tmp_path / "audit.jsonl"}
cells:
  atlas:
    path: {tmp_path / "atlas"}
  cytometer:
    path: {tmp_path / "cytometer"}
"""
    )
    app = create_app(config_yaml)
    return TestClient(app)


def sign_body(secret: str, body: bytes) -> str:
    """Return the value for the `X-Hub-Signature-256` header for `body`."""
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"
