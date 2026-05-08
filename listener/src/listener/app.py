"""FastAPI app: `/github` webhook receiver + `/health` endpoint."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request, status

from listener.config import ListenerConfig
from listener.routing import cell_for_repo
from listener.triggers import handle_merge
from listener.webhook import PullRequestEvent, verify_signature


def create_app(config_path: Path) -> FastAPI:
    config = ListenerConfig.from_file(config_path)
    app = FastAPI(title="colony listener")

    @app.get("/health")
    async def health() -> dict[str, object]:
        return {
            "status": "ok",
            "cells": sorted(config.cells.keys()),
            "audit_log": str(config.audit_log_path),
        }

    @app.post("/github")
    async def github_webhook(
        request: Request,
        x_hub_signature_256: str | None = Header(default=None),
        x_github_event: str | None = Header(default=None),
    ) -> dict[str, object]:
        body = await request.body()

        if not verify_signature(config.webhook_secret, body, x_hub_signature_256):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid signature")

        if x_github_event != "pull_request":
            return {"ignored": True, "reason": f"unhandled event {x_github_event!r}"}

        try:
            event = PullRequestEvent.model_validate_json(body)
        except Exception as exc:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail=f"invalid payload: {exc}"
            ) from exc

        if event.action != "closed" or not event.pull_request.merged:
            return {
                "ignored": True,
                "reason": f"action={event.action} merged={event.pull_request.merged}",
            }

        cell = cell_for_repo(config, event.repository.full_name)
        if cell is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"no cell registered for repo {event.repository.full_name}",
            )

        await handle_merge(
            config=config,
            cell=cell,
            pr_number=event.pull_request.number,
            merge_sha=event.pull_request.merge_commit_sha,
            pr_title=event.pull_request.title,
            pr_author=event.pull_request.user.get("login", "unknown"),
        )
        return {"ok": True, "cell": cell.name}

    return app
