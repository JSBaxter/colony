"""Map a GitHub repo full_name to a cell config entry."""

from __future__ import annotations

from listener.config import CellConfig, ListenerConfig


def cell_for_repo(config: ListenerConfig, repo_full_name: str) -> CellConfig | None:
    """Look up a cell by the trailing segment of `owner/repo`.

    The operator may install the App under any owner; only the repo name
    matters for routing. Returns `None` if no cell is configured for this
    repo.
    """
    repo_name = repo_full_name.rsplit("/", maxsplit=1)[-1]
    return config.cells.get(repo_name)
