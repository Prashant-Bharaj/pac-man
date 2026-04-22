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
    ) -> None:
        """Draw the full level: maze, pellets, ghosts, player.

        Args:
            screen: Pygame surface to draw on.
            level: Current level state.
            tick: Frame counter used for animation timing.
        """
        self._draw_maze(screen, level)
        self._draw_pellets(screen, level, tick)
        self._draw_ghosts(screen, level, tick)
        self._draw_player(screen, level, tick)

    # ------------------------------------------------------------------
    # Maze
    # ------------------------------------------------------------------

    def _draw_maze(
        self, screen: pygame.Surface, level: "Level"
    ) -> None:
        cs = self.cell_size
        for row in range(level.grid_height):
            for col in range(level.grid_width):
                rx, ry = col * cs, row * cs
                if level.grid[row][col] == CellType.WALL:
                    pygame.draw.rect(
                        screen, _WALL, (rx, ry, cs, cs)
                    )
                    if cs >= 8:
                        pygame.draw.rect(
                            screen,
                            _WALL_INNER,
                            (rx + 1, ry + 1, cs - 2, cs - 2),
                        )

    # ------------------------------------------------------------------
    # Pellets
    # ------------------------------------------------------------------

    def _draw_pellets(
        self, screen: pygame.Surface, level: "Level", tick: int
    ) -> None:
        cs = self.cell_size
        for pellet in level.pellets:
            if pellet.eaten:
                continue
            px = pellet.x * cs + cs // 2
            py = pellet.y * cs + cs // 2
            if pellet.pellet_type == PelletType.SUPER_PACGUM:
                if (tick // 15) % 2 == 0:
                    pygame.draw.circle(
                        screen, _SUPER, (px, py), max(3, cs // 3)
                    )
            else:
                pygame.draw.circle(
                    screen, _PACGUM, (px, py), max(2, cs // 7)
                )

    # ------------------------------------------------------------------
    # Player (animated chomping mouth)
    # ------------------------------------------------------------------

    def _draw_player(
        self, screen: pygame.Surface, level: "Level", tick: int
    ) -> None:
        cs = self.cell_size
        pl = level.player
        cx = pl.x * cs + cs // 2
        cy = pl.y * cs + cs // 2
        r = max(3, cs // 2 - 1)

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
        self, screen: pygame.Surface, level: "Level", tick: int
    ) -> None:
        for idx, ghost in enumerate(level.ghosts):
            if not ghost.is_active():
                continue
            cs = self.cell_size
            cx = ghost.x * cs + cs // 2
            cy = ghost.y * cs + cs // 2
            r = max(3, cs // 2 - 1)

            if ghost.state == GhostState.EDIBLE:
                near_end = ghost.state_timer < 2.0
                flash = near_end and (tick // 10) % 2 == 1
                color: tuple[int, int, int] = (
                    _EDIBLE_FLASH if flash else _EDIBLE
                )
                show_eyes = False
            else:
                color = _GHOST_COLORS[idx % len(_GHOST_COLORS)]
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
