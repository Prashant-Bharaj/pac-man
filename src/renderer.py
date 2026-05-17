"""Pygame renderer — draws maze, entities, and HUD."""

import math
import logging
from typing import TYPE_CHECKING

import pygame

from src.entities.ghost import GhostState
from src.entities.pellet import PelletType
from src.entities.player import Direction
from src.maze import CellType

if TYPE_CHECKING:
    from src.level import Level

logger = logging.getLogger(__name__)

_WALL: tuple[int, int, int] = (0, 0, 180)
_WALL_INNER: tuple[int, int, int] = (20, 20, 220)
_FLOOR: tuple[int, int, int] = (0, 0, 0)
_PACGUM: tuple[int, int, int] = (255, 200, 200)
_SUPER: tuple[int, int, int] = (255, 210, 0)
_PLAYER: tuple[int, int, int] = (255, 255, 0)
_EDIBLE: tuple[int, int, int] = (0, 80, 255)
_EDIBLE_FLASH: tuple[int, int, int] = (200, 200, 255)
_WHITE: tuple[int, int, int] = (255, 255, 255)
_DARK_BLUE: tuple[int, int, int] = (0, 0, 200)
_INVINCIBLE_GHOST: tuple[int, int, int] = (150, 150, 150)
_GHOST_COLORS: list[tuple[int, int, int]] = [
    (230, 0, 0),
    (255, 184, 255),
    (0, 220, 220),
    (255, 184, 82),
]

_DIR_ANGLE: dict[Direction, int] = {
    Direction.RIGHT: 0,
    Direction.DOWN: 90,
    Direction.LEFT: 180,
    Direction.UP: 270,
    Direction.NONE: 0,
}


class Renderer:
    """Handles all pygame draw calls for the game level.

    Args:
        screen_width: Window width in pixels.
        screen_height: Window height in pixels.
        cell_size: Pixel size of one maze cell.
    """

    def __init__(
        self, screen_width: int, screen_height: int, cell_size: int = 16
    ) -> None:
        """Initialise renderer dimensions."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.cell_size = cell_size
        self._maze_surface: pygame.Surface | None = None
        self._maze_grid_id: int | None = None
        logger.debug(
            "Renderer initialised (%dx%d, cell=%d)",
            screen_width, screen_height, cell_size,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def draw_level(
        self,
        screen: pygame.Surface,
        level: "Level",
        tick: int,
        is_invincible: bool = False,
    ) -> None:
        """Draw the full level: maze, pellets, ghosts, player.

        Args:
            screen: Pygame surface to draw on.
            level: Current level state.
            tick: Frame counter used for animation timing.
            is_invincible: Whether the invincible cheat is active.
        """
        self._draw_maze(screen, level)
        self._draw_pellets(screen, level, tick)
        self._draw_ghosts(screen, level, tick, is_invincible)
        self._draw_player(screen, level, tick)

    # ------------------------------------------------------------------
    # Maze
    # ------------------------------------------------------------------

    def _draw_maze(
        self, screen: pygame.Surface, level: "Level"
    ) -> None:
        grid_id = id(level.grid)
        if self._maze_surface is None or self._maze_grid_id != grid_id:
            cell_size = self.cell_size
            surf = pygame.Surface(
                (level.grid_width * cell_size, level.grid_height * cell_size)
            )
            surf.fill(_FLOOR)
            
            # Pass 1: Draw base cells with neighbor-aware rounded corners
            rad = max(1, cell_size // 4)
            in_rad = max(1, rad - 1)
            
            for row in range(level.grid_height):
                for col in range(level.grid_width):
                    cell = level.grid[row][col]
                    if cell in (CellType.WALL, CellType.BLOCK):
                        rx, ry = col * cell_size, row * cell_size
                        
                        # Check neighbors of the SAME type
                        up = row > 0 and level.grid[row - 1][col] == cell
                        down = row < level.grid_height - 1 and level.grid[row + 1][col] == cell
                        left = col > 0 and level.grid[row][col - 1] == cell
                        right = col < level.grid_width - 1 and level.grid[row][col + 1] == cell
                        
                        # Only round corners that are "outer" boundaries of the structure
                        tl = rad if not up and not left else 0
                        tr = rad if not up and not right else 0
                        bl = rad if not down and not left else 0
                        br = rad if not down and not right else 0

                        pygame.draw.rect(
                            surf, _WALL, (rx, ry, cell_size, cell_size),
                            border_top_left_radius=tl,
                            border_top_right_radius=tr,
                            border_bottom_left_radius=bl,
                            border_bottom_right_radius=br
                        )
                        
                        if cell_size >= 8:
                            inner_color = (
                                _WALL_INNER if cell == CellType.BLOCK
                                else _FLOOR
                            )
                            itl = in_rad if not up and not left else 0
                            itr = in_rad if not up and not right else 0
                            ibl = in_rad if not down and not left else 0
                            ibr = in_rad if not down and not right else 0
                            
                            pygame.draw.rect(
                                surf,
                                inner_color,
                                (rx + 1, ry + 1, cell_size - 2, cell_size - 2),
                                border_top_left_radius=itl,
                                border_top_right_radius=itr,
                                border_bottom_left_radius=ibl,
                                border_bottom_right_radius=ibr
                            )
            
            # Pass 2: Draw bridges between adjacent cells of the SAME type
            if cell_size >= 8:
                for row in range(level.grid_height):
                    for col in range(level.grid_width):
                        cell = level.grid[row][col]
                        if cell not in (CellType.WALL, CellType.BLOCK):
                            continue
                        
                        rx, ry = col * cell_size, row * cell_size
                        inner_color = _WALL_INNER if cell == CellType.BLOCK else _FLOOR
                        
                        right_match = col < level.grid_width - 1 and level.grid[row][col + 1] == cell
                        down_match = row < level.grid_height - 1 and level.grid[row + 1][col] == cell
                        diag_match = right_match and down_match and level.grid[row + 1][col + 1] == cell

                        if right_match:
                            pygame.draw.rect(
                                surf, inner_color, (rx + cell_size - 1, ry + 1, 2, cell_size - 2)
                            )
                        if down_match:
                            pygame.draw.rect(
                                surf, inner_color, (rx + 1, ry + cell_size - 1, cell_size - 2, 2)
                            )
                        if diag_match:
                            pygame.draw.rect(
                                surf, inner_color, (rx + cell_size - 1, ry + cell_size - 1, 2, 2)
                            )

            self._maze_surface = surf
            self._maze_grid_id = grid_id
        screen.blit(self._maze_surface, (0, 0))

    # ------------------------------------------------------------------
    # Pellets
    # ------------------------------------------------------------------

    def _draw_pellets(
        self, screen: pygame.Surface, level: "Level", tick: int
    ) -> None:
        cell_size = self.cell_size
        for pellet in level.pellets:
            if pellet.eaten:
                continue
            px = pellet.x * cell_size + cell_size // 2
            py = pellet.y * cell_size + cell_size // 2
            if pellet.pellet_type == PelletType.SUPER_PACGUM:
                if (tick // 15) % 2 == 0:
                    pygame.draw.circle(
                        screen, _SUPER, (px, py), max(3, cell_size // 3)
                    )
            else:
                pygame.draw.circle(
                    screen, _PACGUM, (px, py), max(2, cell_size // 7)
                )

    # ------------------------------------------------------------------
    # Player (animated chomping mouth)
    # ------------------------------------------------------------------

    def _draw_player(
        self, screen: pygame.Surface, level: "Level", tick: int
    ) -> None:
        cell_size = self.cell_size
        pl = level.player
        cx = pl.x * cell_size + cell_size // 2
        cy = pl.y * cell_size + cell_size // 2
        r = max(3, cell_size // 2 - 1)

        # Half-angle oscillates 0 → 40 → 0 over 20 frames
        phase = tick % 20
        half_mouth = abs(phase - 10) * 4

        pygame.draw.circle(screen, _PLAYER, (cx, cy), r)
        if half_mouth > 2:
            facing = _DIR_ANGLE.get(pl.direction, 0)
            pts = self._wedge_pts(
                cx, cy, r + 1, facing, float(half_mouth), 8
            )
            pygame.draw.polygon(screen, _FLOOR, pts)

    def _wedge_pts(
        self,
        cx: int,
        cy: int,
        r: int,
        facing: int,
        half_deg: float,
        steps: int,
    ) -> list[tuple[int, int]]:
        """Return polygon vertices for the open-mouth wedge.

        Args:
            cx, cy: Centre of the player circle.
            r: Radius (slightly larger than player radius).
            facing: Direction the mouth faces in degrees (0=right).
            half_deg: Half the mouth opening angle in degrees.
            steps: Number of arc interpolation steps.

        Returns:
            List of (x, y) polygon vertices forming the mouth wedge.
        """
        pts: list[tuple[int, int]] = [(cx, cy)]
        start = math.radians(facing - half_deg)
        end = math.radians(facing + half_deg)
        for i in range(steps + 1):
            a = start + (end - start) * i / steps
            pts.append((
                int(cx + r * math.cos(a)),
                int(cy + r * math.sin(a)),
            ))
        return pts

    # ------------------------------------------------------------------
    # Ghosts
    # ------------------------------------------------------------------

    def _draw_ghosts(
        self, screen: pygame.Surface, level: "Level", tick: int, is_invincible: bool = False
    ) -> None:
        for ghost in level.ghosts:
            if not ghost.is_active():
                continue
            cell_size = self.cell_size
            cx = ghost.x * cell_size + cell_size // 2
            cy = ghost.y * cell_size + cell_size // 2
            r = max(3, cell_size // 2 - 1)

            if ghost.state == GhostState.EDIBLE:
                near_end = ghost.state_timer < 2.0
                flash = near_end and (tick // 10) % 2 == 1
                color: tuple[int, int, int] = (
                    _EDIBLE_FLASH if flash else _EDIBLE
                )
                show_eyes = False
            elif is_invincible:
                color = _INVINCIBLE_GHOST
                show_eyes = True
            else:
                color = _GHOST_COLORS[ghost.ghost_id % len(_GHOST_COLORS)]
                show_eyes = True

            self._draw_ghost(screen, cx, cy, r, color, show_eyes)

    def _draw_ghost(
        self,
        screen: pygame.Surface,
        cx: int,
        cy: int,
        r: int,
        color: tuple[int, int, int],
        show_eyes: bool,
    ) -> None:
        # Dome: circle shifted upward so the ghost fits the cell
        dome_cy = cy - r // 4
        pygame.draw.circle(screen, color, (cx, dome_cy), r)

        # Body: rectangle below the dome centre
        body_h = r + r // 3
        pygame.draw.rect(
            screen, color, (cx - r, dome_cy, r * 2, body_h)
        )

        # Wavy skirt: three floor-coloured bumps at the bottom
        bottom = dome_cy + body_h
        br = max(2, r // 3)
        spread = (r * 2 - br * 2)
        for j in range(3):
            bx = cx - r + br + j * spread // 2
            pygame.draw.circle(screen, _FLOOR, (bx, bottom), br)

        # Eyes (skipped when edible)
        if show_eyes and r >= 5:
            er = max(2, r // 3)
            ey = dome_cy - r // 4
            for ex in [cx - r // 3, cx + r // 3]:
                pygame.draw.circle(screen, _WHITE, (ex, ey), er)
                pygame.draw.circle(
                    screen, _DARK_BLUE, (ex, ey), max(1, er // 2)
                )
