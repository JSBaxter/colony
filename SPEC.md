# colony — design spec

> Container orchestration for the cell colony. Living spec — implement against this.

## Purpose

Colony is the cell that operates other cells. It runs colony-level services (atlas, morphogen, eventually a listener service) as long-lived containers, manages their network and storage, and gives the operator a single `docker compose` interface to bring the whole infrastructure up or down.

It is not itself a colony-level *service* — it's a *tooling* cell. Its primary artifacts are compose files, Dockerfiles, and (eventually) the listener service code.

## Position in the colony

Colony has no runtime dependency on other cells. Its compose file references `atlas` and `morphogen` via sibling-path build contexts; it assumes those cells exist at `~/Documents/repos/cells/<name>/` on the operator's machine.

## Architecture

### Services

| Service     | Image source           | Port  | Volume          | Status            |
|-------------|------------------------|-------|-----------------|-------------------|
| atlas       | `../atlas`             | 8484  | `atlas-data`    | Pending Dockerfile (atlas implementation in progress) |
| morphogen   | `../morphogen`         | 8485  | `morphogen-data`| Pending cell spawn + Dockerfile |
| listener    | `./listener`           | 8486  | —               | Phase 2 (deferred — see end of spec) |

### Network

Single bridge network `colony-net`. All services on it. Nothing exposed beyond `localhost` until TLS / reverse proxy is set up — solo-dev posture for now.

### Volumes

Named Docker volumes for service state. Persisted across container restarts. **No shared workspace volume yet** — cells exchange artifacts via URL pointers in morphogen payloads (S3, GitHub raw, etc.) rather than direct filesystem sharing. Revisit if a concrete need surfaces.

### Bootstrap order

`atlas` → `morphogen` → `listener`. `depends_on` enforces start order; services are runtime-independent (morphogen still works if atlas restarts — see atlas's cross-cell architecture note).

## Per-cell Dockerfile contract

Each service cell ships its own `Dockerfile` at its repo root. Contract:

- Builds an image that runs the cell's MCP server with **HTTP transport**.
- `EXPOSE`s the cell's documented port (atlas: 8484, morphogen: 8485).
- Default command runs the server bound to `0.0.0.0` on the documented port, with the database path set to the mounted volume location (`/var/<cell>/<cell>.db`).
- Image is buildable from the cell's repo root with no additional context.

If a service cell lacks a Dockerfile, `docker compose build <service>` will fail with a clear error and motivate completing the upstream work. This is intentional — Dockerfile ownership stays with the cell, not with colony.

## Operator workflow

```bash
cd ~/Documents/repos/cells/colony
docker compose build       # builds images from sibling cell repos
docker compose up -d       # starts atlas + morphogen
curl http://localhost:8484/health   # verify atlas
curl http://localhost:8485/health   # verify morphogen
```

Cells running on the host (cytometer, in-cell agents) connect to atlas/morphogen via `http://localhost:8484/mcp` and `http://localhost:8485/mcp`.

Tear down:

```bash
docker compose down        # stops services; preserves volumes
docker compose down -v     # nukes volumes (rare; loses all atlas/morphogen state)
```

## Phase 2 — listener service

A small Python service that:

1. Receives GitHub webhooks on `:8486`
2. Validates HMAC signature against `~/.config/colony-bot/webhook_secret`
3. Parses `pull_request.closed` events with `merged: true`
4. Looks up the cell by repo name → identifies the cell's container
5. Triggers a fresh Claude Code session: `docker exec cell-<name> claude -p "claim next task"`
6. Logs everything for audit

Lives at `./listener/` inside this repo as a third docker-compose service alongside atlas + morphogen. **Not its own cell yet** — small (~150 LoC), tightly coupled to colony's orchestration. If it grows (multi-event types, dispatch logic, observability), promote to a cell called **reflex** (automatic stimulus response — biologically accurate).

For solo+localhost dev, the operator uses [smee.io](https://smee.io/) or [ngrok](https://ngrok.com/) to relay GitHub webhooks → `localhost:8486`. Once colony is hosted on a server with a public URL, the relay isn't needed.

## Decisions locked

1. **Containers per service cell**, not per agent. Cell agents (Claude Code) currently run on the operator host; only the long-lived services run in containers. Container-per-agent is a future move when multi-cell concurrency becomes painful.
2. **Sibling-path build context** for atlas + morphogen. Assumes colocated repos. For multi-host later, switch to image registry.
3. **No shared workspace volume** in v1. Artifact passing via URLs in morphogen payloads.
4. **Solo + localhost** for now. Remote hosting is a follow-up after security tightening.
5. **Bot identity gates approval**, not workflow. Branch protection requires bot-authored PRs to be approved by operator before merge; the workflow rule "exit after PR" is documented in CONTRIBUTING.md and per-cell HANDOFF.md.

## Open questions

1. **Health check endpoint convention** for atlas/morphogen — `/health`, `/healthz`, or something else? Pick one and put it in atlas's SPEC.md as a contract.
2. **Service discovery beyond localhost** — when colony moves to a server, hostnames change; cell `.mcp.json` files would need to be parameterized. Worth a small wrapper script when remote hosting becomes real.
3. **TLS** — trivial on localhost (skip), serious work on a public host. Plan with remote hosting.
4. **Per-cell agent containers** — the template's `include_agent_container` option (currently false everywhere) generates an agent-runs-Claude-Code container. When we want sandboxed parallel agent sessions, opt cells in.
