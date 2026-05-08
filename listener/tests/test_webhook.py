"""Tests for HMAC verification + payload parsing via the FastAPI route."""

from __future__ import annotations

import json
from typing import Any

from fastapi.testclient import TestClient

from .conftest import sign_body


def _pr_payload(
    repo: str = "JSBaxter/atlas",
    merged: bool = True,
    action: str = "closed",
) -> dict[str, Any]:
    return {
        "action": action,
        "repository": {"full_name": repo},
        "pull_request": {
            "number": 42,
            "merged": merged,
            "merge_commit_sha": "deadbeef" * 5,
            "title": "test PR",
            "user": {"login": "jb-colony-bot"},
        },
    }


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "atlas" in body["cells"]
    assert "cytometer" in body["cells"]


def test_pr_merged_routes_to_cell(client: TestClient, webhook_secret: str) -> None:
    body = json.dumps(_pr_payload()).encode()
    r = client.post(
        "/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sign_body(webhook_secret, body),
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True, "cell": "atlas"}


def test_invalid_signature_rejected(client: TestClient) -> None:
    body = json.dumps(_pr_payload()).encode()
    r = client.post(
        "/github",
        content=body,
        headers={
            "X-Hub-Signature-256": "sha256=" + "0" * 64,
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 401


def test_missing_signature_rejected(client: TestClient) -> None:
    body = json.dumps(_pr_payload()).encode()
    r = client.post(
        "/github",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 401


def test_pr_not_merged_ignored(client: TestClient, webhook_secret: str) -> None:
    body = json.dumps(_pr_payload(merged=False)).encode()
    r = client.post(
        "/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sign_body(webhook_secret, body),
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 200
    assert r.json()["ignored"] is True


def test_pr_opened_ignored(client: TestClient, webhook_secret: str) -> None:
    body = json.dumps(_pr_payload(action="opened")).encode()
    r = client.post(
        "/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sign_body(webhook_secret, body),
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 200
    assert r.json()["ignored"] is True


def test_unknown_event_ignored(client: TestClient, webhook_secret: str) -> None:
    body = json.dumps({"zen": "Anything added dilutes everything else."}).encode()
    r = client.post(
        "/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sign_body(webhook_secret, body),
            "X-GitHub-Event": "ping",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 200
    assert r.json()["ignored"] is True


def test_unknown_repo_returns_404(client: TestClient, webhook_secret: str) -> None:
    body = json.dumps(_pr_payload(repo="JSBaxter/notarealcell")).encode()
    r = client.post(
        "/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sign_body(webhook_secret, body),
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 404
