"""Tests for the maze adapter."""

from src.maze import (
    CellType,
    generate_maze,
    grid_size,
    is_corridor,
    _fallback_maze,
    _expand,
)


def test_generate_returns_correct_expanded_size() -> None:
    """Expanded grid is (2H+1) x (2W+1)."""
    maze = generate_maze(width=10, height=10, seed=42)
    cols, rows = grid_size(maze)
    assert cols == 21
    assert rows == 21


def test_generate_non_square() -> None:
    """Expanded grid dimensions are correct for non-square input."""
    maze = generate_maze(width=8, height=12, seed=42)
    cols, rows = grid_size(maze)
    assert cols == 17
    assert rows == 25


def test_outer_border_is_all_walls() -> None:
    """The outermost ring of cells is always walls."""
    maze = generate_maze(width=10, height=10, seed=42)
    cols, rows = grid_size(maze)
    for c in range(cols):
        assert maze[0][c] == CellType.WALL
        assert maze[rows - 1][c] == CellType.WALL
    for r in range(rows):
        assert maze[r][0] == CellType.WALL
        assert maze[r][cols - 1] == CellType.WALL


def test_cell_centres_are_corridors() -> None:
    """Every logical cell centre (2r+1, 2c+1) is a corridor."""
    width, height = 10, 10
    maze = generate_maze(width=width, height=height, seed=42)
    for r in range(height):
        for c in range(width):
            assert maze[2 * r + 1][2 * c + 1] == CellType.CORRIDOR


def test_deterministic_with_same_seed() -> None:
    """Same seed produces identical maze."""
    maze1 = generate_maze(width=10, height=10, seed=42)
    maze2 = generate_maze(width=10, height=10, seed=42)
    assert maze1 == maze2


def test_different_seeds_differ() -> None:
    """Different seeds produce different mazes."""
    maze1 = generate_maze(width=10, height=10, seed=42)
    maze2 = generate_maze(width=10, height=10, seed=99)
    assert maze1 != maze2


def test_grid_size() -> None:
    """grid_size returns (cols, rows) correctly."""
    maze = generate_maze(width=6, height=8, seed=1)
    cols, rows = grid_size(maze)
    assert cols == 13
    assert rows == 17


def test_is_corridor_cell_centre() -> None:
    """Logical cell centres are reported as corridors."""
    maze = generate_maze(width=10, height=10, seed=42)
    assert is_corridor(maze, 1, 1) is True


def test_is_corridor_outer_wall() -> None:
    """Outer border cells are not corridors."""
    maze = generate_maze(width=10, height=10, seed=42)
    assert is_corridor(maze, 0, 0) is False


def test_is_corridor_out_of_bounds() -> None:
    """Out-of-bounds coordinates return False without raising."""
    maze = generate_maze(width=10, height=10, seed=42)
    assert is_corridor(maze, -1, 0) is False
    assert is_corridor(maze, 999, 999) is False


def test_fallback_maze_size() -> None:
    """Fallback maze has correct expanded dimensions."""
    maze = _fallback_maze(8, 6)
    assert len(maze) == 13
    assert len(maze[0]) == 17


def test_fallback_maze_outer_walls() -> None:
    """Fallback maze has solid outer walls."""
    maze = _fallback_maze(5, 5)
    rows, cols = len(maze), len(maze[0])
    for c in range(cols):
        assert maze[0][c] == CellType.WALL
        assert maze[rows - 1][c] == CellType.WALL
    for r in range(rows):
        assert maze[r][0] == CellType.WALL
        assert maze[r][cols - 1] == CellType.WALL


def test_fallback_maze_interior_corridors() -> None:
    """Fallback maze interior is all corridors."""
    maze = _fallback_maze(5, 5)
    rows, cols = len(maze), len(maze[0])
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            assert maze[r][c] == CellType.CORRIDOR


def test_expand_single_cell() -> None:
    """A 1x1 cell grid with all walls open expands to a 3x3 corridor centre."""
    cell_grid = [[0b1111]]
    maze = _expand(cell_grid, width=1, height=1)
    assert maze[1][1] == CellType.CORRIDOR
    assert maze[0][0] == CellType.WALL
