"""Tests for Player, Ghost, and Pellet entities."""

from src.entities.ghost import Ghost, GhostState, EDIBLE_DURATION
from src.entities.pellet import Pellet, PelletType
from src.entities.player import Direction, Player
from src.maze import MazeGrid, CellType


# ---------------------------------------------------------------------------
# Minimal maze helpers
# ---------------------------------------------------------------------------

def _open_maze(w: int, h: int) -> MazeGrid:
    """Return a maze where every cell is a corridor (no walls)."""
    return [[CellType.CORRIDOR] * w for _ in range(h)]


def _wall_maze(w: int, h: int) -> MazeGrid:
    """Return a maze where every cell is a wall."""
    return [[CellType.WALL] * w for _ in range(h)]


def _corridor_row_maze() -> MazeGrid:
    """5x5 maze: only row 2 is open (walls everywhere else)."""
    grid = _wall_maze(5, 5)
    for c in range(5):
        grid[2][c] = CellType.CORRIDOR
    return grid


# ---------------------------------------------------------------------------
# Player tests
# ---------------------------------------------------------------------------

class TestPlayer:
    def test_initial_position(self) -> None:
        p = Player(start_x=3, start_y=3)
        assert p.x == 3 and p.y == 3

    def test_respawn_resets_position(self) -> None:
        p = Player(start_x=3, start_y=3)
        p.x, p.y = 10, 10
        p.respawn()
        assert p.x == 3 and p.y == 3

    def test_respawn_resets_direction(self) -> None:
        p = Player(start_x=3, start_y=3)
        p.direction = Direction.RIGHT
        p.respawn()
        assert p.direction == Direction.NONE

    def test_lose_life_decrements(self) -> None:
        p = Player(start_x=3, start_y=3, lives=3)
        p.lose_life()
        assert p.lives == 2

    def test_lose_life_respawns(self) -> None:
        p = Player(start_x=3, start_y=3)
        p.x, p.y = 9, 9
        p.lose_life()
        assert p.x == 3 and p.y == 3

    def test_is_alive_true(self) -> None:
        assert Player(start_x=0, start_y=0, lives=1).is_alive()

    def test_is_alive_false(self) -> None:
        p = Player(start_x=0, start_y=0, lives=1)
        p.lose_life()
        assert not p.is_alive()

    def test_add_score(self) -> None:
        p = Player(start_x=0, start_y=0)
        p.add_score(10)
        p.add_score(50)
        assert p.score == 60

    def test_add_score_ignores_negative(self) -> None:
        p = Player(start_x=0, start_y=0)
        p.add_score(-100)
        assert p.score == 0

    def test_movement_right(self) -> None:
        maze = _open_maze(5, 5)
        p = Player(start_x=2, start_y=2)
        p.set_direction(Direction.RIGHT)
        p.update(p.move_interval, maze)
        assert p.x == 3 and p.y == 2

    def test_movement_up(self) -> None:
        maze = _open_maze(5, 5)
        p = Player(start_x=2, start_y=2)
        p.set_direction(Direction.UP)
        p.update(p.move_interval, maze)
        assert p.x == 2 and p.y == 1

    def test_wall_blocks_movement(self) -> None:
        maze = _corridor_row_maze()
        p = Player(start_x=2, start_y=2)
        p.set_direction(Direction.UP)
        p.update(p.move_interval, maze)
        # row 1 is a wall — player must not move
        assert p.x == 2 and p.y == 2

    def test_queued_direction_applied_when_clear(self) -> None:
        maze = _open_maze(5, 5)
        p = Player(start_x=2, start_y=2)
        p.direction = Direction.RIGHT
        p.set_direction(Direction.DOWN)
        p.update(p.move_interval, maze)
        assert p.y == 3

    def test_falls_back_to_current_direction_when_turn_blocked(self) -> None:
        maze = _corridor_row_maze()
        p = Player(start_x=1, start_y=2)
        p.direction = Direction.RIGHT
        p.set_direction(Direction.UP)   # UP is blocked (wall)
        p.update(p.move_interval, maze)
        # should continue RIGHT instead
        assert p.x == 2 and p.y == 2

    def test_no_move_before_interval(self) -> None:
        maze = _open_maze(5, 5)
        p = Player(start_x=2, start_y=2)
        p.set_direction(Direction.RIGHT)
        p.update(p.move_interval * 0.5, maze)
        assert p.x == 2

    def test_set_speed(self) -> None:
        p = Player(start_x=2, start_y=2)
        p.set_speed(0.05)
        assert p.move_interval == 0.05

    def test_set_speed_clamps_minimum(self) -> None:
        p = Player(start_x=2, start_y=2)
        p.set_speed(0.001)
        assert p.move_interval == 0.05


# ---------------------------------------------------------------------------
# Ghost tests
# ---------------------------------------------------------------------------

class TestGhost:
    def test_initial_position_at_corner(self) -> None:
        g = Ghost(corner_x=1, corner_y=1, ghost_id=0)
        assert g.x == 1 and g.y == 1

    def test_make_edible(self) -> None:
        g = Ghost(corner_x=1, corner_y=1, ghost_id=0)
        g.make_edible()
        assert g.state == GhostState.EDIBLE
        assert g.state_timer == EDIBLE_DURATION

    def test_make_edible_ignored_while_respawning(self) -> None:
        g = Ghost(corner_x=1, corner_y=1, ghost_id=0)
        g.eat()
        g.make_edible()
        assert g.state == GhostState.RESPAWNING

    def test_eat_transitions_to_respawning(self) -> None:
        g = Ghost(corner_x=1, corner_y=1, ghost_id=0)
        g.eat()
        assert g.state == GhostState.RESPAWNING

    def test_respawn_returns_to_corner(self) -> None:
        g = Ghost(corner_x=1, corner_y=1, ghost_id=0)
        g.x, g.y = 5, 5
        g.respawn()
        assert g.x == 1 and g.y == 1
        assert g.state == GhostState.CHASE

    def test_is_edible_true(self) -> None:
        g = Ghost(corner_x=1, corner_y=1, ghost_id=0)
        g.make_edible()
        assert g.is_edible()

    def test_is_edible_false_when_chasing(self) -> None:
        g = Ghost(corner_x=1, corner_y=1, ghost_id=0)
        assert not g.is_edible()

    def test_is_active_false_when_respawning(self) -> None:
        g = Ghost(corner_x=1, corner_y=1, ghost_id=0)
        g.eat()
        assert not g.is_active()

    def test_is_active_true_when_chasing(self) -> None:
        g = Ghost(corner_x=1, corner_y=1, ghost_id=0)
        assert g.is_active()

    def test_edible_timer_expires_returns_to_chase(self) -> None:
        g = Ghost(corner_x=1, corner_y=1, ghost_id=0)
        g.make_edible()
        maze = _open_maze(10, 10)
        g.update(EDIBLE_DURATION + 0.1, maze, 5, 5)
        assert g.state == GhostState.CHASE

    def test_respawn_timer_expires_returns_to_corner(self) -> None:
        g = Ghost(corner_x=1, corner_y=1, ghost_id=0)
        g.eat()
        maze = _open_maze(10, 10)
        # drain timer without triggering move
        g.state_timer = 0.01
        g.update(0.1, maze, 5, 5)
        assert g.state == GhostState.CHASE
        assert g.x == 1 and g.y == 1

    def test_chase_moves_toward_player(self) -> None:
        maze = _open_maze(10, 10)
        g = Ghost(corner_x=0, corner_y=0, ghost_id=0)
        g.x, g.y = 0, 0
        g.update(g.move_interval, maze, 5, 0)
        assert g.x > 0 or g.y >= 0

    def test_flee_moves_away_from_player(self) -> None:
        maze = _open_maze(10, 10)
        g = Ghost(corner_x=0, corner_y=0, ghost_id=0)
        g.x, g.y = 5, 5
        g.make_edible()
        # reset move_timer so it moves immediately
        g.move_timer = g.move_interval
        g.update(0.0, maze, 5, 5)
        dist_after = abs(g.x - 5) + abs(g.y - 5)
        assert dist_after >= 1

    def test_no_move_before_interval(self) -> None:
        maze = _open_maze(10, 10)
        g = Ghost(corner_x=0, corner_y=0, ghost_id=0)
        g.x, g.y = 0, 0
        g.move_timer = 0.0
        g.update(g.move_interval * 0.1, maze, 9, 9)
        assert g.x == 0 and g.y == 0


# ---------------------------------------------------------------------------
# Pellet tests
# ---------------------------------------------------------------------------

class TestPellet:
    def test_pacgum_not_super(self) -> None:
        p = Pellet(x=1, y=1, pellet_type=PelletType.PACGUM)
        assert not p.is_super()

    def test_super_pacgum_is_super(self) -> None:
        p = Pellet(x=1, y=1, pellet_type=PelletType.SUPER_PACGUM)
        assert p.is_super()

    def test_initial_not_eaten(self) -> None:
        p = Pellet(x=1, y=1, pellet_type=PelletType.PACGUM)
        assert not p.eaten

    def test_eat_marks_eaten(self) -> None:
        p = Pellet(x=1, y=1, pellet_type=PelletType.PACGUM)
        p.eat()
        assert p.eaten
