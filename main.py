"""Entry point for the Pac-Man game.

Usage:
    python3 main.py [config.json]
"""

import asyncio
import os
import sys

from src.config import load_config
from src.game import Game


def _default_config_path() -> str:
    # When frozen by PyInstaller, _MEIPASS is the temp bundle directory.
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "config.json")


async def main() -> None:
    """Parse arguments, load config, and launch the game."""
    if len(sys.argv) == 1:
        config_path = _default_config_path()
    elif len(sys.argv) == 2:
        config_path = sys.argv[1]
    else:
        print("Usage: pac-man [config.json]")
        sys.exit(1)

    config = load_config(config_path)
    game = Game(config)
    await game.run()


# asyncio.run at module level so pygbag (web build) picks it up correctly.
# Works identically on desktop.
asyncio.run(main())
