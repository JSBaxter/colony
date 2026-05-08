# colony listener

Webhook receiver for cross-cell trigger events. **Observe-and-notify only**
for now — does not auto-spawn agents; see "Why this doesn't auto-spawn
Claude" below.

## What it does

1. Listens for GitHub webhooks on `POST /github` (default port `8486`)
2. Verifies HMAC signatures via the App's webhook secret
3. Parses `pull_request.closed` events with `merged: true`
4. Routes by repo full_name → cell (config-driven)
5. Per-cell `asyncio.Lock` (same-cell triggers serialize, cross-cell parallelize)
6. Appends the event to a JSONL audit log
7. Prints a human-readable line + rings the terminal bell on stdout

## Setup

```bash
cd listener
uv sync
cp config.example.yml config.yml
$EDITOR config.yml      # set cells map, webhook_secret_file path
```

Set the App's webhook secret on the GitHub App settings page, then save the
same value to `~/.config/colony-bot/webhook_secret` (`chmod 600`).

Run:

```bash
uv run python -m listener
# or with custom port / host:
uv run python -m listener --host 0.0.0.0 --port 8486
```

## Webhook tunneling for local dev

GitHub can't reach `localhost`. Use [smee.io](https://smee.io):

```bash
# Create a channel at https://smee.io/new — note the URL.
# Set the GitHub App's "Webhook URL" to the smee URL.
# Then on your laptop, run a relay:
npx smee-client -u https://smee.io/<channel-id> -t http://localhost:8486/github
```

Or [ngrok](https://ngrok.com/) for a real public URL when you want one.

## Audit log

Every trigger appends one JSON object per line to the path in `config.yml`:

```bash
tail -f ~/.local/state/colony/listener/triggers.jsonl | jq
```

## Tests

```bash
uv run pytest
```

## Why this doesn't auto-spawn Claude

Short version: `claude -p "..."` (print mode) had a billing-routing bug
([anthropics/claude-code#43333](https://github.com/anthropics/claude-code/issues/43333),
fixed 2026-04-08) that silently routed Pro/Max OAuth credentials through
per-token API billing. Then on 2026-04-04 Anthropic introduced a
"third-party harness" classification that left subprocess-spawning
`claude` from a backend in undocumented eligibility territory
([#56250](https://github.com/anthropics/claude-code/issues/56250) is open
asking exactly this question).

For a Pro/Max subscriber, getting this wrong is potentially financially
catastrophic. So this MVP **observes and notifies**:

1. The listener logs the merge and rings the terminal bell.
2. You manually run `dev-tools/agent-container/run.sh claude` in the cell
   (interactive — safe under subscription billing).
3. The agent reads its queue, finds the next claimable task, proceeds per
   `CONTRIBUTING.md`.

When [#56250](https://github.com/anthropics/claude-code/issues/56250) gets
answered, this evolves to actually `docker exec <cell>-agent claude -p`
automatically. Until then, the operator stays in the loop.

## Architecture notes

- **Host process for now.** Containerizing the listener adds docker-out-of-docker
  complexity (so it can `docker exec` cell agent-containers) without
  letting us auto-spawn anyway. Revisit when phase 2 (auto-trigger)
  becomes real.
- **No persistence beyond the JSONL.** A future iteration could record
  triggers in a sqlite DB or push them into each cell's queue via MCP.
  For MVP, the log is enough — operator reads it, decides what to do.
- **No retry logic.** GitHub webhooks have their own redelivery; the
  listener doesn't add a second layer.
