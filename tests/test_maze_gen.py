
from src.maze import generate_maze, grid_size, CellType

def test():
    width, height = 10, 10
    seed = 42
    maze = generate_maze(width, height, seed)
    w, h = grid_size(maze)
    print(f"Maze size: {w}x{h}")
    
    # Check if it's all corridors (which _fallback_maze would produce if it's large)
    # _fallback_maze(10, 10) would be 21x21 with outer walls.
    
    wall_count = 0
    corridor_count = 0
    for row in maze:
        for cell in row:
            if cell in (CellType.WALL, CellType.BLOCK):
                wall_count += 1
            else:
                corridor_count += 1
    
    print(f"Walls: {wall_count}, Corridors: {corridor_count}")
    
    # In a fallback maze, walls are only on the border.
    # Border walls for 21x21: 21 + 21 + 19 + 19 = 80
    if wall_count == 80:
        print("This looks like a fallback maze!")
    else:
        print("This looks like a generated maze!")

if __name__ == "__main__":
    test()
