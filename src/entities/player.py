"""Pac-Man player entity."""

import logging
from dataclasses import dataclass, field
from enum import Enum

from src.maze import MazeGrid, is_corridor

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
        start_x: Starting column in the expanded maze grid.
        start_y: Starting row in the expanded maze grid.
        lives: Number of starting lives.
    """

    start_x: int
    start_y: int
    lives: int = 3
    x: int = field(init=False)
    y: int = field(init=False)
    score: int = field(init=False, default=0)
    direction: Direction = field(init=False, default=Direction.NONE)
    next_direction: Direction = field(init=False, default=Direction.NONE)
    move_timer: float = field(init=False, default=0.0)
    move_interval: float = field(init=False, default=0.15)

    def __post_init__(self) -> None:
        """Initialize position to start coordinates."""
        self.x = self.start_x
        self.y = self.start_y

    def respawn(self) -> None:
        """Reset player to starting position after losing a life."""
        self.x = self.start_x
        self.y = self.start_y
        self.direction = Direction.NONE
        self.next_direction = Direction.NONE
        self.move_timer = 0.0

    def lose_life(self) -> None:
        """Decrement life count and respawn."""
        self.lives -= 1
        logger.debug("Player lost a life. Lives remaining: %d", self.lives)
        self.respawn()

    def is_alive(self) -> bool:
        """Return True if the player has lives remaining.

        Returns:
            True when lives > 0.
        """
        return self.lives > 0

    def add_score(self, points: int) -> None:
        """Add points to the player's score.

        Args:
            points: Non-negative integer to add.
        """
        self.score += max(0, points)

    def set_direction(self, direction: Direction) -> None:
        """Queue a direction change to be applied on the next valid move.

        Args:
            direction: Desired movement direction.
        """
        self.next_direction = direction

    def update(self, dt: float, maze: MazeGrid) -> None:
        """Advance movement timer and move one cell when ready.

        Tries to turn into next_direction first; falls back to the
        current direction if the turn is blocked.

        Args:
            dt: Delta time in seconds since last update.
            maze: The current level's maze grid for wall checking.
        """
        self.move_timer += dt
        if self.move_timer < self.move_interval:
            return
        self.move_timer = 0.0

        if self._try_move(self.next_direction, maze):
            self.direction = self.next_direction
        else:
            self._try_move(self.direction, maze)

    def _try_move(self, direction: Direction, maze: MazeGrid) -> bool:
        """Attempt to move one cell in the given direction.

        Args:
            direction: Direction to attempt.
            maze: Maze grid for corridor checking.

        Returns:
            True if the move succeeded.
        """
        dx, dy = direction.value
        if dx == 0 and dy == 0:
            return False
        nx, ny = self.x + dx, self.y + dy
        if is_corridor(maze, nx, ny):
            self.x = nx
            self.y = ny
            return True
        return False

    def set_speed(self, interval: float) -> None:
        """Override the move interval (used by cheat speed boost).

        Args:
            interval: Seconds between cell moves (lower = faster).
        """
        self.move_interval = max(0.05, interval)
