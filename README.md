# colony

Container orchestration for the cell colony. Brings up atlas, morphogen, and the listener service via docker compose; cells in the colony connect to these as remote MCP servers.

## Start here

- **Identity & principles:** `MANIFESTO.md`
- **Rules for contributing (human or agent):** `CONTRIBUTING.md`
- **How to verify a change:** `TESTING.md`
- **Current operational truth:** `STATE.md`
- **Recurring process activities:** `CEREMONIES.md`
- **How this cell was born + how to spawn a sibling:**
  `REPRODUCTION.md`
- **Release history:** `CHANGELOG.md`

Agents: `CLAUDE.md` and `AGENTS.md` both point back at
`CONTRIBUTING.md` and `MANIFESTO.md` — those are the sources of
truth.

## Bootstrap

```bash
cd ~/Documents/repos/cells/colony
docker compose build       # builds images from sibling cell repos
docker compose up -d       # starts atlas + morphogen
curl http://localhost:8484/health   # verify atlas
curl http://localhost:8485/health   # verify morphogen
```

Atlas and morphogen Dockerfiles live in their own cell repos
(`../atlas/Dockerfile`, `../morphogen/Dockerfile`); colony just
orchestrates. If a service is unimplemented its build fails with a
clear error — that's the gate motivating the upstream work.

Full architecture and per-cell Dockerfile contract: [`SPEC.md`](./SPEC.md).

## Agent sessions per cell (Remote Control)

Each cell runs a long-lived `claude remote-control` session inside its
own agent container. The Claude mobile app's **Code** tab lists every
running session — tap a cell to dispatch a task to it from your phone.

```bash
# one-time per cell — OAuth state then persists in the named volume:
docker compose -f docker-compose.agents.yml build
docker compose -f docker-compose.agents.yml run --rm agent-atlas bash
#   inside the container:
claude /login        # browser opens; complete OAuth
exit

# bring all agent sessions up:
docker compose -f docker-compose.agents.yml up -d
```

Each container runs `claude remote-control --spawn=session --name <cell>`
as its main process. Subscription billing only — Anthropic's Remote
Control rejects API keys. See [`SPEC.md`](./SPEC.md) for the architectural
rationale (why this replaced the original "listener auto-spawns
`claude -p`" plan).

## Listener (audit-only)

Webhook receiver for cross-cell PR-merge events. **No longer the
trigger mechanism** — Remote Control + the mobile app handle that.
The listener stays as an audit log: every PR merge across the colony
appends a JSONL record + rings the terminal bell, useful for
observability when several cells are churning. Runs as a host process.
See [`listener/README.md`](./listener/README.md) for setup.

```bash
cd listener
uv sync
cp config.example.yml config.yml && $EDITOR config.yml
uv run python -m listener
```

## Active directories / files

- `docker-compose.yml`
  Colony-level **services**: atlas + morphogen as long-lived MCP
  servers on a private `colony-net` bridge network with named
  persistent volumes.
- `docker-compose.agents.yml`
  Per-cell **agent sessions**: one `claude remote-control` container
  per cell, each registering as a session in the Claude mobile app's
  Code tab. Different lifecycle from services compose — agent
  sessions get started/stopped per development effort, services run
  continuously.
- `compose.override.example.yml`
  Local-dev overrides template. Copy to `compose.override.yml`
  (gitignored) for personal tweaks (live-reload mounts, log levels).
- `listener/`
  Webhook receiver service. Audit log of cross-cell PR-merge events.
  Self-contained Python project (FastAPI + uvicorn) under `uv`.
- `dev-tools/`
  Local-only tooling. Houses the bundled `queue/` MCP server (Python
  via uv), `agent-container/` (Docker image used by both the agents
  compose and ad-hoc `run.sh` invocations), and `agent-bot/` (GitHub
  App bot identity wrappers used by agents to author commits and PRs).

## Reproduction

This cell was scaffolded from the
[`stem-cell`](https://github.com/JSBaxter/stem-cell).
The exact template version this cell tracks is recorded in
`.copier-answers.yml`. See `REPRODUCTION.md` for how to spawn a
sibling cell or pull template updates.

## Notes

- Local secrets and build state are gitignored.
