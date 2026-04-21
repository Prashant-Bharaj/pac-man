"""Pac-Man player entity."""

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Direction(Enum):
    """Movement direction for the player."""

    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    NONE = (0, 0)


@dataclass
class Player:
    """Pac-Man player state and movement logic.

    Args:
        start_x: Starting column in maze grid.
        start_y: Starting row in maze grid.
        lives: Number of starting lives.
    """

    start_x: int
    start_y: int
    lives: int = 3
    x: int = field(init=False)
    y: int = field(init=False)
    score: int = field(init=False, default=0)
    direction: Direction = field(init=False, default=Direction.NONE)

    def __post_init__(self) -> None:
        """Initialize position to start coordinates."""
        self.x = self.start_x
        self.y = self.start_y

    def respawn(self) -> None:
        """Reset player to starting position after losing a life."""
        self.x = self.start_x
        self.y = self.start_y
        self.direction = Direction.NONE

    def lose_life(self) -> None:
        """Decrement life count and respawn."""
        self.lives -= 1
        logger.debug("Player lost a life. Lives remaining: %d", self.lives)
        self.respawn()

    def is_alive(self) -> bool:
        """Return True if the player has lives remaining."""
        return self.lives > 0

    def add_score(self, points: int) -> None:
        """Add points to the player's score.

        Args:
            points: Non-negative integer to add.
        """
        self.score += max(0, points)
