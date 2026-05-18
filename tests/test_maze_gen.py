"""Smoke tests for assigned maze generation."""

from src.maze import generate_maze, grid_size, CellType


def test_generate_maze_uses_assigned_generator() -> None:
    """Generated mazes should not look like the simple fallback grid."""
    width, height = 10, 10
    seed = 42
    maze = generate_maze(width, height, seed)
    w, h = grid_size(maze)

    assert (w, h) == (21, 21)

    # Check if it is all corridors, as _fallback_maze would produce.
    # _fallback_maze(10, 10) would be 21x21 with outer walls.

    wall_count = 0
    corridor_count = 0
    for row in maze:
        for cell in row:
            if cell in (CellType.WALL, CellType.BLOCK):
                wall_count += 1
            else:
                corridor_count += 1

    assert corridor_count > 0
    assert wall_count != 80
