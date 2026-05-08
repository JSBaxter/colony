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

## Listener (observe-and-notify)

Webhook receiver for cross-cell PR-merge events. Runs as a host
process for now (not in compose). See [`listener/README.md`](./listener/README.md)
for setup, the smee.io tunnel for local dev, and the rationale for
why this doesn't auto-spawn Claude yet.

```bash
cd listener
uv sync
cp config.example.yml config.yml && $EDITOR config.yml
uv run python -m listener
```

## Active directories / files

- `docker-compose.yml`
  The orchestration. Defines atlas + morphogen services on a private
  `colony-net` bridge network with named persistent volumes. Listener
  service is intentionally **not** in compose — it runs as a host
  process for the MVP (host-side `docker exec`-ability needed for
  future trigger-spawn pattern).
- `compose.override.example.yml`
  Local-dev overrides template. Copy to `compose.override.yml`
  (gitignored) for personal tweaks (live-reload mounts, log levels).
- `listener/`
  The webhook receiver service. Self-contained Python project
  (FastAPI + uvicorn) under `uv`. See its README for setup.
- `dev-tools/`
  Local-only tooling. Houses the bundled `queue/` MCP server (Python
  via uv), `agent-container/` (Docker image for running Claude Code
  in a bounded container with `bypassPermissions`), and `agent-bot/`
  (GitHub App bot identity wrappers used by agents to author commits
  and PRs).

## Reproduction

This cell was scaffolded from the
[`stem-cell`](https://github.com/JSBaxter/stem-cell).
The exact template version this cell tracks is recorded in
`.copier-answers.yml`. See `REPRODUCTION.md` for how to spawn a
sibling cell or pull template updates.

## Notes

- Local secrets and build state are gitignored.
