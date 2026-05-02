"""Maze adapter wrapping the assigned A-Maze-ing package.

The MazeGenerator produces a cell grid where each value is a bitmask
of open directions (bit 0=N, bit 1=S, bit 2=W, bit 3=E). This module
expands that into a pixel-style MazeGrid of CellType values suitable
for Pac-Man: a (2H+1) x (2W+1) grid where walls are solid blocks and
corridors are walkable spaces.

Falls back to a minimal open maze on any generator error.
"""

import logging
from enum import Enum

logger = logging.getLogger(__name__)

# Bitmask constants for open wall directions
_NORTH: int = 1
_SOUTH: int = 2
_WEST: int = 4
_EAST: int = 8


class CellType(Enum):
    """Possible states for a maze cell."""

    WALL = 0
    CORRIDOR = 1


MazeGrid = list[list[CellType]]


def _fallback_maze(width: int, height: int) -> MazeGrid:
    """Return a minimal valid open maze when the generator fails.

    Builds a (2H+1) x (2W+1) grid with outer walls and all
    interior cells open as corridors.

    Args:
        width: Number of logical maze columns.
        height: Number of logical maze rows.

    Returns:
        A MazeGrid with only outer walls.
    """
    rows = 2 * height + 1
    cols = 2 * width + 1
    grid: MazeGrid = []
    for r in range(rows):
        line: list[CellType] = []
        for c in range(cols):
            if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                line.append(CellType.WALL)
            else:
                line.append(CellType.CORRIDOR)
        grid.append(line)
    return grid


def _expand(cell_grid: list[list[int]], width: int, height: int) -> MazeGrid:
    """Expand a bitmask cell grid into a wall/corridor pixel grid.

    Each logical cell (r, c) becomes pixel (2r+1, 2c+1). Passages
    between cells are opened based on the directional bitmask. The
    resulting grid is (2H+1) x (2W+1) with a solid outer wall border.

    Args:
        cell_grid: 2D list of bitmask ints from MazeGenerator.
        width: Number of logical columns.
        height: Number of logical rows.

    Returns:
        Expanded MazeGrid of CellType values.
    """
    rows = 2 * height + 1
    cols = 2 * width + 1

    grid: MazeGrid = [
        [CellType.WALL] * cols for _ in range(rows)
    ]

    for r in range(height):
        for c in range(width):
            cell = cell_grid[r][c]
            pr = 2 * r + 1
            pc = 2 * c + 1

            grid[pr][pc] = CellType.CORRIDOR

            if cell & _NORTH and r > 0:
                grid[pr - 1][pc] = CellType.CORRIDOR
            if cell & _SOUTH and r < height - 1:
                grid[pr + 1][pc] = CellType.CORRIDOR
            if cell & _WEST and c > 0:
                grid[pr][pc - 1] = CellType.CORRIDOR
            if cell & _EAST and c < width - 1:
                grid[pr][pc + 1] = CellType.CORRIDOR

    return grid


def generate_maze(
    width: int, height: int, seed: int, perfect: bool = False
) -> MazeGrid:
    """Generate a maze using the assigned A-Maze-ing package.

    The returned grid is (2*height+1) x (2*width+1) — callers should
    use this expanded size for entity placement, not the raw width/height.

    Args:
        width: Desired number of logical maze columns.
        height: Desired number of logical maze rows.
        seed: RNG seed for deterministic generation.
        perfect: If False, produces Pac-Man-compatible looping corridors.

    Returns:
        Expanded MazeGrid of CellType values.
    """
    try:
        from mazegenerator.mazegenerator import MazeGenerator
        mg = MazeGenerator(size=(width, height), perfect=perfect, seed=seed)
        return _expand(mg.maze, width, height)
    except ImportError:
        logger.error(
            "A-Maze-ing package not installed — using fallback maze"
        )
    except (AttributeError, IndexError, RuntimeError, ValueError) as exc:
        logger.error(
            "Maze generation failed: %s — using fallback maze", exc
        )

    return _fallback_maze(width, height)


def grid_size(maze: MazeGrid) -> tuple[int, int]:
    """Return (width, height) in cells of an expanded MazeGrid.

    Args:
        maze: A MazeGrid produced by generate_maze.

    Returns:
        Tuple of (number of columns, number of rows).
    """
    return len(maze[0]), len(maze)


def is_corridor(maze: MazeGrid, x: int, y: int) -> bool:
    """Return True if the cell at (x, y) is a walkable corridor.

    Args:
        maze: A MazeGrid produced by generate_maze.
        x: Column index.
        y: Row index.

    Returns:
        True if the cell is CORRIDOR and within bounds.
    """
    cols, rows = grid_size(maze)
    if x < 0 or y < 0 or x >= cols or y >= rows:
        return False
    return maze[y][x] == CellType.CORRIDOR
