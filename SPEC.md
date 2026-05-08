# colony — design spec

> Container orchestration for the cell colony. Living spec — implement against this.

## Purpose

Colony is the cell that operates other cells. It does two related things:

1. **Runs colony-level services** (atlas, morphogen) as long-lived containers — the cells in the colony talk to these as remote MCP servers.
2. **Hosts the per-cell agent containers** — each cell has a long-running `claude remote-control` session in its own container, which the operator dispatches tasks to from the Claude mobile app's Code tab.

It is not itself a colony-level *service* — it's a *tooling* cell. Its primary artifacts are compose files, Dockerfiles, and the listener service (now audit-only).

## Position in the colony

Colony has no runtime dependency on other cells. Its compose file references `atlas` and `morphogen` via sibling-path build contexts; it assumes those cells exist at `~/Documents/repos/cells/<name>/` on the operator's machine.

## Architecture

### Services

| Service     | Image source           | Port  | Volume          | Status            |
|-------------|------------------------|-------|-----------------|-------------------|
| atlas       | `../atlas`             | 8484  | `atlas-data`    | Pending Dockerfile (atlas implementation in progress) |
| morphogen   | `../morphogen`         | 8485  | `morphogen-data`| Pending cell spawn + Dockerfile |
| listener    | (host process)         | 8486  | —               | Built; audit-only role (see "Listener" section) |

### Per-cell agent sessions (`docker-compose.agents.yml`)

A separate compose file runs one `claude remote-control` container per cell, registered with the Claude mobile app.

| Container     | Image source                                    | Cell repo bind  |
|---------------|-------------------------------------------------|-----------------|
| agent-atlas   | `../atlas/dev-tools/agent-container/Dockerfile` | `../atlas`      |
| agent-cytometer | `../cytometer/dev-tools/agent-container/Dockerfile` | `../cytometer` |
| (more as cells are spawned)                                                       | |

Each container's CMD is `claude remote-control --spawn=session --name <cell>`. Subscription billing only — Anthropic's Remote Control rejects API keys. Per-cell named volumes hold the agent's `~/.claude` state (OAuth + session memory) so containers can be torn down and restarted without re-auth.

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

## Trigger mechanism — Anthropic Remote Control + mobile app

Earlier drafts of this spec assumed the listener would auto-spawn agents via subprocess (`claude -p`). That plan died on contact with Anthropic's billing-routing landscape: `claude -p` had a documented bug ([anthropics/claude-code#43333](https://github.com/anthropics/claude-code/issues/43333), since fixed) that routed Pro/Max OAuth credentials through per-token API billing, and the April 2026 "third-party harness" classification ([#56250](https://github.com/anthropics/claude-code/issues/56250), open) left subprocess-spawning eligibility undocumented. For a Pro/Max subscriber, getting this wrong is potentially financially catastrophic.

**The replacement is Anthropic's Remote Control feature** ([docs](https://code.claude.com/docs/en/remote-control)). Each cell runs `claude remote-control --spawn=session` inside its agent container. The session registers via outbound HTTPS with the Anthropic API and waits for connections. The Claude mobile app lists all running sessions in a "Code" tab. After a PR merges, the operator taps the cell's session and dispatches "continue with the next task" — the desktop session does the work, opens the next PR, and goes back to idle awaiting the next dispatch.

This sidesteps the billing risk entirely (Remote Control is subscription-billed, no API path). It also removes the need for any locally-built trigger machinery — the listener's original "auto-spawn on merge" purpose is now Anthropic's responsibility.

## Listener — audit only

The listener still ships at `./listener/` as a FastAPI host process. Its role is now **audit-log only**: receive GitHub webhooks, verify HMAC, append PR-merge events to a JSONL log, ring a terminal bell. Useful for observability when several cells are churning and you want a single `tail -f` view of what merged where.

It runs as a host process (not in compose) because it's small enough that containerizing adds more friction than value, and the trigger problem it was originally built to solve no longer needs solving by us.

If we ever need real autonomy (e.g. PR merges trigger a fresh session without operator tap), promotion path: swap the listener's "log" action for a real subprocess invocation once [#56250](https://github.com/anthropics/claude-code/issues/56250) clarifies and harness-mode billing is officially safe. Until then, the manual-dispatch loop is the right shape.

## Decisions locked

1. **Containers per service AND per agent.** Two compose files, two lifecycles: services compose for atlas + morphogen (long-lived MCP daemons), agents compose for one `claude remote-control` container per cell (long-lived agent session). Earlier drafts kept agents on the operator host; that flipped once Remote Control made phone-first operation viable.
2. **Sibling-path build context** for both compose files. Assumes colocated repos at `~/Documents/repos/cells/<name>/`. For multi-host later, switch to image registry.
3. **No shared workspace volume** in v1. Artifact passing via URLs in morphogen payloads. Per-cell named volumes for `~/.claude` state and the queue's `.venv` give isolation without sharing.
4. **Solo + localhost** for now. Remote hosting is a follow-up after security tightening.
5. **Bot identity gates approval**, not workflow. Branch protection requires bot-authored PRs to be approved by operator before merge; the workflow rule "exit after PR" is documented in CONTRIBUTING.md and per-cell HANDOFF.md.
6. **Subscription billing only.** Both for service cells (they don't call Claude at all) and agent containers (Remote Control rejects API keys; we don't pass `ANTHROPIC_API_KEY` into containers). One accidental API run on a Pro/Max account can exceed a year of subscription cost; the architecture is shaped to make accidental API billing structurally impossible.

## Open questions

1. **Health check endpoint convention** for atlas/morphogen — `/health`, `/healthz`, or something else? Pick one and put it in atlas's SPEC.md as a contract.
2. **Service discovery beyond localhost** — when colony moves to a server, hostnames change; cell `.mcp.json` files would need to be parameterized. Worth a small wrapper script when remote hosting becomes real.
3. **TLS** — trivial on localhost (skip), serious work on a public host. Plan with remote hosting.
4. **UID mismatch between host and container.** The bind-mount of `~/.config/colony-bot/` (chmod 600 files on host) into agent containers assumes the host operator's uid matches the in-container `agent` uid (1000). This holds for most personal Linux setups but breaks for hosts where the operator's uid differs. Workaround is to rebuild the cell's agent-container image with `useradd ... --uid <host-uid>`. Worth surfacing in the agent-container README so it doesn't catch operators by surprise.
