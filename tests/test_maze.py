"""Tests for the maze adapter."""

from src.maze import (
    CellType,
    generate_maze,
    generate_visible_maze,
    grid_size,
    is_corridor,
    _fallback_maze,
    _expand,
)

FT_SMALL_PATTERN = [
    [1, 0, 0, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1],
    [0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 1, 1],
]


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


def test_generate_visible_maze_exact_size() -> None:
    """Visible maze API returns exactly requested dimensions."""
    for width, height in [
        (7, 7),
        (8, 8),
        (10, 10),
        (10, 13),
        (13, 10),
        (20, 20),
        (21, 21),
    ]:
        maze = generate_visible_maze(width, height, seed=42)
        cols, rows = grid_size(maze)
        assert cols == width
        assert rows == height


def test_generate_visible_maze_keeps_outer_walls() -> None:
    """Exact visible mazes keep a solid outer wall."""
    maze = generate_visible_maze(width=10, height=13, seed=42)
    cols, rows = grid_size(maze)
    for c in range(cols):
        assert maze[0][c] == CellType.WALL
        assert maze[rows - 1][c] == CellType.WALL
    for r in range(rows):
        assert maze[r][0] == CellType.WALL
        assert maze[r][cols - 1] == CellType.WALL


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


def test_expand_opens_normal_cell_centres() -> None:
    """Logical cells that are not fully blocked become corridors."""
    maze = _expand([[0]], width=1, height=1)
    assert maze[1][1] == CellType.CORRIDOR


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


def test_expand_preserves_fully_blocked_cell() -> None:
    """A fully closed package cell remains a block in the expanded maze."""
    maze = _expand([[0b1111]], width=1, height=1)
    assert maze[1][1] == CellType.BLOCK
    assert maze[0][0] == CellType.BLOCK
    assert maze[2][2] == CellType.BLOCK


def test_expand_opens_passage_when_shared_wall_is_absent() -> None:
    """Missing wall bits open passages between neighboring cells."""
    maze = _expand([[0, 0]], width=2, height=1)
    assert maze[1][1] == CellType.CORRIDOR
    assert maze[1][2] == CellType.CORRIDOR
    assert maze[1][3] == CellType.CORRIDOR


def test_expand_keeps_passage_closed_when_shared_wall_exists() -> None:
    """Present wall bits keep neighboring cells separated."""
    maze = _expand([[0b1000, 0b0100]], width=2, height=1)
    assert maze[1][1] == CellType.CORRIDOR
    assert maze[1][2] == CellType.WALL
    assert maze[1][3] == CellType.CORRIDOR


def test_generate_visible_maze_preserves_42_pattern() -> None:
    """The package's blocked 42 pattern remains visible in large mazes."""
    visible_width = 50
    visible_height = 50
    logical_width = (visible_width - 1) // 2
    logical_height = (visible_height - 1) // 2
    pattern_x = int((logical_width - len(FT_SMALL_PATTERN[0])) / 2)
    pattern_y = int((logical_height - len(FT_SMALL_PATTERN)) / 2)

    maze = generate_visible_maze(visible_width, visible_height, seed=42)

    open_pattern_centres = 0
    for y, row in enumerate(FT_SMALL_PATTERN):
        for x, value in enumerate(row):
            grid_y = 2 * (pattern_y + y) + 1
            grid_x = 2 * (pattern_x + x) + 1
            if value:
                assert maze[grid_y][grid_x] == CellType.BLOCK
            elif maze[grid_y][grid_x] == CellType.CORRIDOR:
                open_pattern_centres += 1

    assert open_pattern_centres > 0
