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

## Active directories / files

- `docker-compose.yml`
  The orchestration. Defines atlas + morphogen services on a private
  `colony-net` bridge network with named persistent volumes. Listener
  service (phase 2) is stubbed out and commented.
- `compose.override.example.yml`
  Local-dev overrides template. Copy to `compose.override.yml`
  (gitignored) for personal tweaks (live-reload mounts, log levels).
- `dev-tools/`
  Local-only tooling. Houses the bundled `queue/` MCP server (used
  by any agent working on this cell — though most colony work is
  operator config, not agent code) and `agent-bot/` (GitHub App bot
  identity wrappers; activates when phase 2 listener service work
  needs PRs).

## Reproduction

This cell was scaffolded from the
[`stem-cell`](https://github.com/JSBaxter/stem-cell).
The exact template version this cell tracks is recorded in
`.copier-answers.yml`. See `REPRODUCTION.md` for how to spawn a
sibling cell or pull template updates.

## Notes

- Local secrets and build state are gitignored.
