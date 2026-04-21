"""Core game loop and state machine — stub for Phase 5."""

import logging
from enum import Enum, auto

from src.config import GameConfig

logger = logging.getLogger(__name__)


class GameState(Enum):
    """Top-level game state machine states."""

    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    NAME_ENTRY = auto()
    QUIT = auto()


class Game:
    """Orchestrates the game loop and state transitions.

    Args:
        config: Validated game configuration.
    """

    def __init__(self, config: GameConfig) -> None:
        """Initialise game with given config."""
        self.config = config
        self.state = GameState.MAIN_MENU
        logger.info("Game initialised with %d levels", len(config.levels))

    def run(self) -> None:
        """Start and run the main game loop until the player quits."""
        logger.info("Game loop starting (stub — pygame not yet initialised)")
