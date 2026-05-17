"""Maze adapter wrapping the assigned A-Maze-ing package.

The MazeGenerator produces a cell grid where each value is a bitmask
of closed walls (bit 0=N, bit 1=S, bit 2=W, bit 3=E). This module
expands that into a pixel-style MazeGrid of CellType values suitable
for Pac-Man: a (2H+1) x (2W+1) grid where walls are solid blocks and
corridors are walkable spaces.

Falls back to a minimal open maze on any generator error.
"""

import logging
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# Bitmask constants for closed wall directions.
_NORTH: int = 1
_SOUTH: int = 2
_WEST: int = 4
_EAST: int = 8
_ALL_WALLS: int = _NORTH | _SOUTH | _WEST | _EAST


class CellType(Enum):
    """Possible states for a maze cell."""

    WALL = 0
    CORRIDOR = 1
    BLOCK = 2


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


def _fallback_visible_maze(width: int, height: int) -> MazeGrid:
    """Return an exact-size open maze with solid outer walls.

    Args:
        width: Desired visible grid width.
        height: Desired visible grid height.

    Returns:
        A MazeGrid with exactly height rows and width columns.
    """
    grid: MazeGrid = []
    for r in range(height):
        line: list[CellType] = []
        for c in range(width):
            if r == 0 or r == height - 1 or c == 0 or c == width - 1:
                line.append(CellType.WALL)
            else:
                line.append(CellType.CORRIDOR)
        grid.append(line)
    return grid


def _expand(cell_grid: list[list[int]], width: int, height: int) -> MazeGrid:
    """Expand a bitmask cell grid into a wall/corridor pixel grid.

    Each logical cell (r, c) becomes pixel (2r+1, 2c+1). A missing
    wall bit opens a passage in that direction. Fully closed cells are
    preserved as blocked cells, which keeps the package's 42 pattern
    visible when the maze is large enough to contain it. The
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

            if cell == _ALL_WALLS:
                # Fill the 3x3 logical cell block with BLOCK type
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        gr, gc = pr + dr, pc + dc
                        if 0 <= gr < rows and 0 <= gc < cols:
                            grid[gr][gc] = CellType.BLOCK
                continue

            grid[pr][pc] = CellType.CORRIDOR

            if (
                not (cell & _NORTH)
                and r > 0
                and cell_grid[r - 1][c] != _ALL_WALLS
            ):
                grid[pr - 1][pc] = CellType.CORRIDOR
            if (
                not (cell & _SOUTH)
                and r < height - 1
                and cell_grid[r + 1][c] != _ALL_WALLS
            ):
                grid[pr + 1][pc] = CellType.CORRIDOR
            if (
                not (cell & _WEST)
                and c > 0
                and cell_grid[r][c - 1] != _ALL_WALLS
            ):
                grid[pr][pc - 1] = CellType.CORRIDOR
            if (
                not (cell & _EAST)
                and c < width - 1
                and cell_grid[r][c + 1] != _ALL_WALLS
            ):
                grid[pr][pc + 1] = CellType.CORRIDOR

    return grid


def _fit_to_visible_size(
    expanded: MazeGrid, width: int, height: int
) -> MazeGrid:
    """Fit an expanded odd-sized maze into an exact visible grid.

    The expanded maze is never larger than the requested visible grid.
    When an even visible size leaves an extra interior row or column,
    that edge is opened from adjacent corridors while the outer border
    remains solid.
    """
    rows = len(expanded)
    cols = len(expanded[0])
    grid: MazeGrid = [
        [CellType.WALL] * width for _ in range(height)
    ]

    skip_right_border = width > cols
    skip_bottom_border = height > rows

    for r in range(min(rows, height)):
        if skip_bottom_border and r == rows - 1:
            continue
        for c in range(min(cols, width)):
            if skip_right_border and c == cols - 1:
                continue
            grid[r][c] = expanded[r][c]

    if skip_right_border:
        edge_x = width - 2
        source_x = max(1, edge_x - 1)
        for r in range(1, height - 1):
            if grid[r][source_x] == CellType.CORRIDOR:
                grid[r][edge_x] = CellType.CORRIDOR

    if skip_bottom_border:
        edge_y = height - 2
        source_y = max(1, edge_y - 1)
        for c in range(1, width - 1):
            if grid[source_y][c] == CellType.CORRIDOR:
                grid[edge_y][c] = CellType.CORRIDOR

    return grid


def _iterative_generate_maze(
    self: Any, x: int, y: int, from_code: int
) -> None:
    """Iterative replacement for MazeGenerator._generate_maze.

    Replaces the library's recursive DFS with a stack to avoid Python
    call-stack overhead (~841 frames for 29x29). Preserves exact traversal
    order and random behavior by keeping each cell's _get_neighbors generator
    in the stack so it resumes where it left off after backtracking.
    """
    self._path[y][x] = 1
    non_mutable = self._maze[y][x]
    self._maze[y][x] = 15 & ~from_code
    stack = [(x, y, non_mutable, self._get_neighbors(x, y))]

    while stack:
        cx, cy, nm, nbrs = stack[-1]
        for nx, ny, code, opp_code in nbrs:
            if code & nm:
                continue
            self._maze[cy][cx] &= ~code
            self._path[ny][nx] = 1
            new_nm = self._maze[ny][nx]
            self._maze[ny][nx] = 15 & ~opp_code
            stack.append((nx, ny, new_nm, self._get_neighbors(nx, ny)))
            break
        else:
            stack.pop()


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
        # _find_short_path runs an IDDFS up to width*height iterations and
        # blocks the main thread for seconds on larger mazes. We never read
        # MazeGenerator.shortest_path, so skip it entirely.
        MazeGenerator._find_short_path = lambda self: None
        # _generate_maze is a recursive DFS; at 29x29 that's ~841 Python
        # stack frames. Replace with an iterative version to avoid the
        # per-frame overhead.
        MazeGenerator._generate_maze = _iterative_generate_maze
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


def generate_visible_maze(
    width: int, height: int, seed: int, perfect: bool = False
) -> MazeGrid:
    """Generate a maze with exact visible dimensions.

    Args:
        width: Desired final grid width.
        height: Desired final grid height.
        seed: RNG seed for deterministic generation.
        perfect: If False, produces Pac-Man-compatible looping corridors.

    Returns:
        MazeGrid with exactly height rows and width columns.
    """
    if width < 3 or height < 3:
        logger.error(
            "Visible maze size %dx%d is too small — using fallback maze",
            width,
            height,
        )
        return _fallback_visible_maze(max(3, width), max(3, height))

    logical_width = max(1, (width - 1) // 2)
    logical_height = max(1, (height - 1) // 2)
    expanded = generate_maze(
        logical_width,
        logical_height,
        seed=seed,
        perfect=perfect,
    )
    return _fit_to_visible_size(expanded, width, height)


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
