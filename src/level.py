"""Level setup, update loop, and collision detection."""

import logging
import random
from dataclasses import dataclass, field
from enum import Enum, auto

from src.cheat import CheatMode
from src.config import GameConfig, LevelConfig
from src.entities.ghost import Ghost
from src.entities.pellet import Pellet, PelletType
from src.entities.player import Player
from src.maze import MazeGrid, generate_maze, grid_size, is_corridor

logger = logging.getLogger(__name__)

SPEED_NORMAL: float = 0.15
SPEED_BOOST: float = 0.08


class LevelEvent(Enum):
    """Events produced by Level.update() each frame."""

    PACGUM_EATEN = auto()
    SUPER_PACGUM_EATEN = auto()
    GHOST_EATEN = auto()
    PLAYER_HIT = auto()
    GAME_OVER = auto()
    LEVEL_COMPLETE = auto()
    TIMEOUT = auto()


@dataclass
class Level:
    """A fully initialised game level.

    Args:
        index: Zero-based level number.
        config: Global game config.
        level_cfg: Per-level config (width, height, seed).
        starting_lives: Override lives from config (for level continuity).
        starting_score: Score carried in from previous levels.
    """

    index: int
    config: GameConfig
    level_cfg: LevelConfig
    starting_lives: int | None = None
    starting_score: int = 0
    grid: MazeGrid = field(init=False)
    grid_width: int = field(init=False)
    grid_height: int = field(init=False)
    player: Player = field(init=False)
    ghosts: list[Ghost] = field(init=False)
    pellets: list[Pellet] = field(init=False)
    time_remaining: float = field(init=False)

    def __post_init__(self) -> None:
        """Build maze and place all entities."""
        self.time_remaining = float(self.config.level_max_time)
        # Use config seed for level 0; subsequent levels use random seeds
        # to ensure a unique experience on every playthrough.
        if self.index == 0:
            seed = self.level_cfg.seed
        else:
            seed = random.randint(0, 2**31 - 1)

        self.grid = generate_maze(
            self.level_cfg.width,
            self.level_cfg.height,
            seed=seed,
            perfect=False,
        )
        self.grid_width, self.grid_height = grid_size(self.grid)
        self._place_entities()

    def _place_entities(self) -> None:
        """Place player, ghosts, and pellets on the expanded maze grid."""
        w = self.grid_width
        h = self.grid_height
        cx, cy = w // 2, h // 2

        if not is_corridor(self.grid, cx, cy):
            cx = cx + 1 if cx % 2 == 0 else cx
            cy = cy + 1 if cy % 2 == 0 else cy

        lives = (
            self.starting_lives if self.starting_lives is not None
            else self.config.lives
        )
        self.player = Player(start_x=cx, start_y=cy, lives=lives)
        self.player.score = self.starting_score

        corner_candidates = [
            (1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2),
        ]
        corners = [
            (x, y) for x, y in corner_candidates
            if is_corridor(self.grid, x, y)
        ]
        while len(corners) < 4:
            corners.append(corners[0] if corners else (1, 1))

        self.ghosts = [
            Ghost(corner_x=gx, corner_y=gy, ghost_id=i)
            for i, (gx, gy) in enumerate(corners[:4])
        ]

        corner_set = set(corners[:4])
        self.pellets = []
        for row in range(h):
            for col in range(w):
                if not is_corridor(self.grid, col, row):
                    continue
                if (col, row) == (cx, cy):
                    continue
                if (col, row) in corner_set:
                    self.pellets.append(Pellet(
                        x=col, y=row,
                        pellet_type=PelletType.SUPER_PACGUM,
                    ))
                else:
                    self.pellets.append(
                        Pellet(x=col, y=row, pellet_type=PelletType.PACGUM)
                    )

    # ------------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------------

    def update(self, dt: float, cheat: CheatMode) -> list[LevelEvent]:
        """Advance one game tick: move entities, check collisions.

        Args:
            dt: Delta time in seconds since last frame.
            cheat: Active cheat flags.

        Returns:
            List of LevelEvent values that occurred this tick.
        """
        events: list[LevelEvent] = []

        self.time_remaining = max(0.0, self.time_remaining - dt)
        if self.time_remaining == 0.0:
            events.append(LevelEvent.TIMEOUT)
            return events

        interval = SPEED_BOOST if cheat.speed_boost else SPEED_NORMAL
        self.player.set_speed(interval)
        self.player.update(dt, self.grid)

        if not cheat.ghost_freeze:
            for ghost in self.ghosts:
                ghost.update(
                    dt, self.grid, self.player.x, self.player.y
                )

        events.extend(self._check_pellet_collisions())

        if self.is_complete():
            events.append(LevelEvent.LEVEL_COMPLETE)
            return events

        if not cheat.invincible:
            events.extend(self._check_ghost_collisions())

        return events

    def _check_pellet_collisions(self) -> list[LevelEvent]:
        """Collect pellets the player is standing on.

        Returns:
            List of PACGUM_EATEN or SUPER_PACGUM_EATEN events.
        """
        events: list[LevelEvent] = []
        for pellet in self.pellets:
            if pellet.eaten:
                continue
            if pellet.x == self.player.x and pellet.y == self.player.y:
                pellet.eat()
                if pellet.is_super():
                    events.append(LevelEvent.SUPER_PACGUM_EATEN)
                    for ghost in self.ghosts:
                        ghost.make_edible()
                else:
                    events.append(LevelEvent.PACGUM_EATEN)
        return events

    def _check_ghost_collisions(self) -> list[LevelEvent]:
        """Check for player–ghost overlap and apply consequences.

        Returns:
            List of GHOST_EATEN, PLAYER_HIT, or GAME_OVER events.
        """
        events: list[LevelEvent] = []
        for ghost in self.ghosts:
            if not ghost.is_active():
                continue
            if ghost.x != self.player.x or ghost.y != self.player.y:
                continue
            if ghost.is_edible():
                ghost.eat()
                events.append(LevelEvent.GHOST_EATEN)
            else:
                self.player.lose_life()
                if self.player.is_alive():
                    events.append(LevelEvent.PLAYER_HIT)
                else:
                    events.append(LevelEvent.GAME_OVER)
                break
        return events

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def remaining_pacgums(self) -> int:
        """Return count of uneaten pellets.

        Returns:
            Number of pellets not yet eaten.
        """
        return sum(1 for p in self.pellets if not p.eaten)

    def is_complete(self) -> bool:
        """Return True when all pellets have been eaten.

        Returns:
            True if no pellets remain.
        """
        return self.remaining_pacgums() == 0

    def pellet_at(self, x: int, y: int) -> Pellet | None:
        """Return the uneaten pellet at (x, y), or None.

        Args:
            x: Column to query.
            y: Row to query.

        Returns:
            Matching Pellet or None.
        """
        for pellet in self.pellets:
            if not pellet.eaten and pellet.x == x and pellet.y == y:
                return pellet
        return None
