"""Maze adapter wrapping the assigned A-Maze-ing package.

Translates the external package output into an internal MazeGrid
(2D list of CellType values). Never raises; falls back to a minimal
valid maze on any generator error.
"""

import logging
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CellType(Enum):
    """Possible states for a maze cell."""

    WALL = 0
    CORRIDOR = 1


MazeGrid = list[list[CellType]]


def _fallback_maze(width: int, height: int) -> MazeGrid:
    """Return a minimal valid open maze when the generator fails.

    Args:
        width: Number of columns.
        height: Number of rows.

    Returns:
        A MazeGrid where all interior cells are CORRIDOR.
    """
    grid: MazeGrid = []
    for row in range(height):
        line: list[CellType] = []
        for col in range(width):
            if row == 0 or row == height - 1 or col == 0 or col == width - 1:
                line.append(CellType.WALL)
            else:
                line.append(CellType.CORRIDOR)
        grid.append(line)
    return grid


def generate_maze(
    width: int, height: int, seed: int, perfect: bool = False
) -> MazeGrid:
    """Generate a maze using the assigned A-Maze-ing package.

    Args:
        width: Desired maze width in cells.
        height: Desired maze height in cells.
        seed: RNG seed for deterministic generation.
        perfect: If False, produces Pac-Man-compatible corridors.

    Returns:
        A 2D MazeGrid of CellType values.
    """
    try:
        from amazeing import Maze  # noqa: PGH003  # type: ignore
        maze_obj: Any = Maze(
            width=width, height=height, seed=seed, perfect=perfect
        )
        maze_obj.generate()
        return _convert(maze_obj, width, height)
    except ImportError:
        logger.error("A-Maze-ing package not installed — using fallback maze")
    except Exception as exc:
        logger.error(
            "Maze generation failed: %s — using fallback maze", exc
        )

    return _fallback_maze(width, height)


def _convert(maze_obj: Any, width: int, height: int) -> MazeGrid:
    """Convert A-Maze-ing output to a MazeGrid.

    The exact conversion depends on the assigned package's interface.
    This function will be updated once the package is inspected.

    Args:
        maze_obj: The maze object returned by the A-Maze-ing package.
        width: Expected width.
        height: Expected height.

    Returns:
        MazeGrid representation of the maze.
    """
    grid: MazeGrid = []
    for row in range(height):
        line: list[CellType] = []
        for col in range(width):
            cell = maze_obj.grid[row][col]
            if cell == 0:
                line.append(CellType.WALL)
            else:
                line.append(CellType.CORRIDOR)
        grid.append(line)
    return grid
