"""Entry point: `python -m listener` boots the FastAPI app via uvicorn."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import uvicorn

from listener.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="colony listener")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(os.environ.get("LISTENER_CONFIG", "config.yml")),
        help="Path to YAML config (default: ./config.yml or $LISTENER_CONFIG).",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8486)
    args = parser.parse_args()

    app = create_app(args.config)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
