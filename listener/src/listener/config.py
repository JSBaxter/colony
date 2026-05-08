"""YAML config loader for the listener.

`cells`: maps a cell name (the trailing segment of a GitHub repo full_name,
e.g. `atlas` for `JSBaxter/atlas`) to the absolute path on disk of that
cell's repo on the operator's machine.

`webhook_secret_file`: path to the file containing the GitHub App webhook
secret. Alternative `webhook_secret` (literal string) is supported for tests
but discouraged in production configs.

`audit_log_path`: where the listener appends its trigger events as JSONL.
Defaults to `~/.local/state/colony/listener/triggers.jsonl`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class CellConfig:
    name: str
    path: Path


@dataclass(frozen=True)
class ListenerConfig:
    cells: dict[str, CellConfig]
    webhook_secret: str
    audit_log_path: Path

    @classmethod
    def from_file(cls, path: Path) -> ListenerConfig:
        data: dict[str, Any] = yaml.safe_load(path.read_text())
        cells = {
            name: CellConfig(name=name, path=Path(entry["path"]).expanduser())
            for name, entry in data.get("cells", {}).items()
        }
        secret = _resolve_secret(data)
        audit_log = Path(
            data.get("audit_log_path", "~/.local/state/colony/listener/triggers.jsonl")
        ).expanduser()
        return cls(cells=cells, webhook_secret=secret, audit_log_path=audit_log)


def _resolve_secret(data: dict[str, Any]) -> str:
    if "webhook_secret_file" in data:
        return Path(data["webhook_secret_file"]).expanduser().read_text().strip()
    if "webhook_secret" in data:
        return str(data["webhook_secret"])
    msg = "config must specify either webhook_secret_file or webhook_secret"
    raise ValueError(msg)
