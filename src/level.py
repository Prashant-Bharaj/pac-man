"""Level setup: maze generation, entity placement."""

import logging
from dataclasses import dataclass, field

from src.config import GameConfig, LevelConfig
from src.entities.ghost import Ghost
from src.entities.pellet import Pellet, PelletType
from src.entities.player import Player
from src.maze import MazeGrid, CellType, generate_maze

logger = logging.getLogger(__name__)


@dataclass
class Level:
    """A fully initialised game level.

    Args:
        index: Zero-based level number.
        config: Global game config.
        level_cfg: Per-level config (width, height, seed).
    """

    index: int
    config: GameConfig
    level_cfg: LevelConfig
    grid: MazeGrid = field(init=False)
    player: Player = field(init=False)
    ghosts: list[Ghost] = field(init=False)
    pellets: list[Pellet] = field(init=False)
    time_remaining: float = field(init=False)

    def __post_init__(self) -> None:
        """Build maze and place all entities."""
        self.time_remaining = float(self.config.level_max_time)
        seed = self.level_cfg.seed if self.index == 0 else None
        self.grid = generate_maze(
            self.level_cfg.width,
            self.level_cfg.height,
            seed=seed if seed is not None else self.index + 1,
            perfect=False,
        )
        self._place_entities()

    def _place_entities(self) -> None:
        """Place player, ghosts, and pellets on the generated maze."""
        w = self.level_cfg.width
        h = self.level_cfg.height
        cx, cy = w // 2, h // 2

        self.player = Player(start_x=cx, start_y=cy, lives=self.config.lives)

        corners = [(1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)]
        self.ghosts = [
            Ghost(corner_x=gx, corner_y=gy, ghost_id=i)
            for i, (gx, gy) in enumerate(corners)
        ]

        self.pellets = []
        corner_set = set(corners)
        for row in range(h):
            for col in range(w):
                is_corridor = self.grid[row][col] == CellType.CORRIDOR
                if is_corridor and (col, row) != (cx, cy):
                    if (col, row) in corner_set:
                        self.pellets.append(Pellet(
                            x=col, y=row,
                            pellet_type=PelletType.SUPER_PACGUM,
                        ))
                    else:
                        self.pellets.append(
                            Pellet(x=col, y=row, pellet_type=PelletType.PACGUM)
                        )

    def remaining_pacgums(self) -> int:
        """Return count of uneaten pacgums (including super-pacgums).

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
