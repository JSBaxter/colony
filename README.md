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

## Active directories

- `dev-tools/`
  Local-only tooling that runs on a developer's machine. Houses
  the bundled `queue/` MCP server, used by every agent working on
  this cell.  And `agent-bot/` (GitHub App bot identity wrappers).
(Add directories here as the cell grows.)

## Reproduction

This cell was scaffolded from the
[`stem-cell`](https://github.com/JSBaxter/stem-cell).
The exact template version this cell tracks is recorded in
`.copier-answers.yml`. See `REPRODUCTION.md` for how to spawn a
sibling cell or pull template updates.

## Notes

- Local secrets and build state are gitignored.
