"""GitHub webhook payload models + HMAC signature verification.

Pydantic models are intentionally permissive (`extra="ignore"`) — GitHub's
webhook payloads are large and field-stable enough that we can pull only
what we need without breaking on additions.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

from pydantic import BaseModel, ConfigDict


class Repository(BaseModel):
    model_config = ConfigDict(extra="ignore")

    full_name: str  # e.g. "JSBaxter/atlas"


class PullRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: int
    merged: bool
    merge_commit_sha: str | None = None
    title: str
    user: dict[str, Any]


class PullRequestEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action: str  # "opened" | "closed" | "synchronize" | ...
    repository: Repository
    pull_request: PullRequest


def verify_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    """Validate `X-Hub-Signature-256` header against `body` using `secret`.

    GitHub sends `sha256=<hex digest>` in the header. Comparison uses
    `hmac.compare_digest` to avoid timing leaks.
    """
    if not signature_header:
        return False
    if not signature_header.startswith("sha256="):
        return False
    expected = signature_header.removeprefix("sha256=")
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, expected)
