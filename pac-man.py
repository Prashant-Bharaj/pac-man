"""Entry point for the Pac-Man game.

Usage:
    python3 pac-man.py config.json
"""

import asyncio
import json
import sys
from pathlib import Path


def _strip_comment_lines(text: str) -> str:
    """Remove config comment lines before syntax preflight."""
    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped.startswith("#") and not stripped.startswith("//"):
            lines.append(line)
    return "\n".join(lines)


def _preflight_config_file(path: str) -> None:
    """Fail early for unreadable or syntactically invalid config files."""
    if Path(path).suffix.lower() != ".json":
        print(f"Error: Config file '{path}' must have a .json extension")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw_text = fh.read()
    except OSError as exc:
        print(f"Error: Cannot open config '{path}': {exc}")
        sys.exit(1)

    try:
        data = json.loads(_strip_comment_lines(raw_text))
    except json.JSONDecodeError as exc:
        print(f"Error: Config '{path}' is not valid JSON: {exc}")
        sys.exit(1)

    if not isinstance(data, dict):
        print(f"Error: Config '{path}' must be a JSON object")
        sys.exit(1)


async def main() -> None:
    """Parse arguments, load config, and launch the game."""
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py config.json")
        sys.exit(1)

    config_path = sys.argv[1]
    _preflight_config_file(config_path)

    from src.config import ConfigLoadError, load_config

    try:
        config = load_config(config_path)
    except ConfigLoadError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    from src.game import Game

    game = Game(config)
    game.run()


# asyncio.run at module level so pygbag (web build) picks it up correctly.
# Works identically on desktop.
asyncio.run(main())
