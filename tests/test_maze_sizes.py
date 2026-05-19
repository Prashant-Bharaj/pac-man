"""Smoke tests for generated maze sizes."""

from src.maze import generate_maze, grid_size, CellType


def test_generate_maze_sizes() -> None:
    """Generated mazes should fit the expected expanded dimensions."""
    sizes = [(20, 20), (21, 21), (10, 10), (100, 100)]
    for w, h in sizes:
        maze = generate_maze(w, h, seed=42)
        mw, mh = grid_size(maze)

        assert (mw, mh) == (2 * w + 1, 2 * h + 1)

        wall_count = sum(
            sum(
                1
                for cell in row
                if cell in (CellType.WALL, CellType.BLOCK)
            )
            for row in maze
        )
        expected_fallback_walls = (2 * w + 1) * 2 + (2 * h + 1 - 2) * 2

        assert wall_count != expected_fallback_walls
