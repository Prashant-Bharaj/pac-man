
from src.maze import generate_maze, grid_size, CellType

def test_sizes():
    sizes = [(20, 20), (21, 21), (10, 10), (100, 100)]
    for w, h in sizes:
        try:
            maze = generate_maze(w, h, seed=42)
            mw, mh = grid_size(maze)
            print(f"Requested {w}x{h}, got {mw}x{mh}")
            
            # Check for fallback
            wall_count = sum(
                sum(1 for cell in row if cell in (CellType.WALL, CellType.BLOCK))
                for row in maze
            )
            expected_fallback_walls = (2*w + 1) * 2 + (2*h + 1 - 2) * 2
            if wall_count == expected_fallback_walls:
                print(f"  Result: FALLBACK (wall count {wall_count})")
            else:
                print(f"  Result: GENERATED (wall count {wall_count})")
        except Exception as e:
            print(f"  Failed with {e}")

if __name__ == "__main__":
    test_sizes()
