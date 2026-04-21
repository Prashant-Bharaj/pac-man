"""Entry point for the Pac-Man game.

Usage:
    python3 pac-man.py config.json
"""

import sys

from src.config import load_config
from src.game import Game


def main() -> None:
    """Parse arguments, load config, and launch the game."""
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py config.json")
        sys.exit(1)

    config = load_config(sys.argv[1])
    game = Game(config)
    game.run()


if __name__ == "__main__":
    main()
