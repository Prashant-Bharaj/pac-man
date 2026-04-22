"""Ghost entity and AI state machine.

Each ghost moves one cell per tick. In CHASE state a BFS finds the
shortest path to the player and the ghost steps along it. In EDIBLE
state the ghost flees — it picks the direction that maximises its
Manhattan distance from the player. In RESPAWNING the ghost is
invisible and returns to its corner before re-entering CHASE.
"""

import logging
import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

from src.maze import MazeGrid, is_corridor

logger = logging.getLogger(__name__)

EDIBLE_DURATION: float = 8.0
RESPAWN_DURATION: float = 7.0

_DIRECTIONS: list[tuple[int, int]] = [(0, -1), (0, 1), (-1, 0), (1, 0)]


class GhostState(Enum):
    """Ghost AI state."""

    CHASE = "chase"
    EDIBLE = "edible"
    RESPAWNING = "respawning"


@dataclass
class Ghost:
    """A single ghost entity with autonomous movement AI.

    Args:
        corner_x: Home corner column in the expanded maze grid.
        corner_y: Home corner row in the expanded maze grid.
        ghost_id: Unique identifier (0–3).
    """

    corner_x: int
    corner_y: int
    ghost_id: int
    x: int = field(init=False)
    y: int = field(init=False)
    state: GhostState = field(init=False, default=GhostState.CHASE)
    state_timer: float = field(init=False, default=0.0)
    move_timer: float = field(init=False, default=0.0)
    move_interval: float = field(init=False, default=0.2)

    def __post_init__(self) -> None:
        """Place ghost at its home corner."""
        self.x = self.corner_x
        self.y = self.corner_y
        # Stagger initial moves so ghosts don't all move in sync
        self.move_timer = self.ghost_id * 0.05

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def make_edible(self) -> None:
        """Transition ghost to edible state."""
        if self.state == GhostState.RESPAWNING:
            return
        self.state = GhostState.EDIBLE
        self.state_timer = EDIBLE_DURATION
        logger.debug("Ghost %d is now edible", self.ghost_id)

    def eat(self) -> None:
        """Ghost was eaten by the player; begin respawn countdown."""
        self.state = GhostState.RESPAWNING
        self.state_timer = RESPAWN_DURATION
        logger.debug(
            "Ghost %d eaten, respawning in %.1fs",
            self.ghost_id, RESPAWN_DURATION,
        )

    def respawn(self) -> None:
        """Return ghost to its home corner in CHASE state."""
        self.x = self.corner_x
        self.y = self.corner_y
        self.state = GhostState.CHASE
        self.state_timer = 0.0
        logger.debug(
            "Ghost %d respawned at corner (%d, %d)",
            self.ghost_id, self.x, self.y,
        )

    def is_edible(self) -> bool:
        """Return True if this ghost can currently be eaten.

        Returns:
            True when state is EDIBLE.
        """
        return self.state == GhostState.EDIBLE

    def is_active(self) -> bool:
        """Return True if the ghost is visible and can collide.

        Returns:
            False only while RESPAWNING.
        """
        return self.state != GhostState.RESPAWNING

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self, dt: float, maze: MazeGrid, player_x: int, player_y: int
    ) -> None:
        """Tick timers, transition states, and move one cell when ready.

        Args:
            dt: Delta time in seconds since last update.
            maze: Current level maze grid.
            player_x: Player's current column.
            player_y: Player's current row.
        """
        if self.state in (GhostState.EDIBLE, GhostState.RESPAWNING):
            self.state_timer -= dt
            if self.state_timer <= 0:
                if self.state == GhostState.EDIBLE:
                    self.state = GhostState.CHASE
                    logger.debug("Ghost %d no longer edible", self.ghost_id)
                else:
                    self.respawn()
                    return

        self.move_timer += dt
        if self.move_timer < self.move_interval:
            return
        self.move_timer = 0.0

        if self.state == GhostState.CHASE:
            self._move_chase(maze, player_x, player_y)
        elif self.state == GhostState.EDIBLE:
            self._move_flee(maze, player_x, player_y)
        elif self.state == GhostState.RESPAWNING:
            self._move_to_corner(maze)

    # ------------------------------------------------------------------
    # Movement strategies
    # ------------------------------------------------------------------

    def _neighbours(
        self, maze: MazeGrid, x: int, y: int
    ) -> list[tuple[int, int]]:
        """Return all walkable neighbours of (x, y).

        Args:
            maze: Maze grid.
            x: Column.
            y: Row.

        Returns:
            List of (nx, ny) corridor cells adjacent to (x, y).
        """
        return [
            (x + dx, y + dy)
            for dx, dy in _DIRECTIONS
            if is_corridor(maze, x + dx, y + dy)
        ]

    def _bfs_next_step(
        self,
        maze: MazeGrid,
        target_x: int,
        target_y: int,
    ) -> tuple[int, int] | None:
        """BFS from current position to target; return first step.

        Args:
            maze: Maze grid.
            target_x: Destination column.
            target_y: Destination row.

        Returns:
            (nx, ny) of the first step toward the target, or None if
            no path exists.
        """
        if (self.x, self.y) == (target_x, target_y):
            return None

        visited: set[tuple[int, int]] = {(self.x, self.y)}
        queue: deque[tuple[tuple[int, int], tuple[int, int] | None]] = deque()
        queue.append(((self.x, self.y), None))

        while queue:
            (cx, cy), first = queue.popleft()
            for nx, ny in self._neighbours(maze, cx, cy):
                step = first or (nx, ny)
                if (nx, ny) == (target_x, target_y):
                    return step
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), step))

        return None

    def _move_wander(
        self, maze: MazeGrid, player_x: int, player_y: int
    ) -> None:
        """Occasionally chase the player via BFS, otherwise move randomly."""
        if random.random() < 0.3:
            step = self._bfs_next_step(maze, player_x, player_y)
            if step:
                self.x, self.y = step
                return
        neighbours = self._neighbours(maze, self.x, self.y)
        if neighbours:
            self.x, self.y = random.choice(neighbours)

    def _move_chase(
        self, maze: MazeGrid, player_x: int, player_y: int
    ) -> None:
        """Move one step toward the player via BFS.

        Ghost 0 (Blinky) always targets the player directly.
        Ghost 1 (Pinky) targets 2 cells ahead of the player.
        Ghosts 2 and 3 wander with occasional BFS chases.

        Args:
            maze: Maze grid.
            player_x: Player's column.
            player_y: Player's row.
        """
        if self.ghost_id >= 2:
            self._move_wander(maze, player_x, player_y)
            return
        target = (player_x, player_y) if self.ghost_id == 0 else (player_x + 2, player_y + 2)
        step = self._bfs_next_step(maze, *target)
        if step:
            self.x, self.y = step
        else:
            neighbours = self._neighbours(maze, self.x, self.y)
            if neighbours:
                self.x, self.y = random.choice(neighbours)

    def _move_flee(
        self, maze: MazeGrid, player_x: int, player_y: int
    ) -> None:
        """Move away from the player by maximising Manhattan distance.

        Args:
            maze: Maze grid.
            player_x: Player's column.
            player_y: Player's row.
        """
        neighbours = self._neighbours(maze, self.x, self.y)
        if not neighbours:
            return
        best = max(
            neighbours,
            key=lambda p: abs(p[0] - player_x) + abs(p[1] - player_y),
        )
        self.x, self.y = best

    def _move_to_corner(self, maze: MazeGrid) -> None:
        """Move toward the ghost's home corner during respawn.

        Args:
            maze: Maze grid.
        """
        step = self._bfs_next_step(maze, self.corner_x, self.corner_y)
        if step:
            self.x, self.y = step
