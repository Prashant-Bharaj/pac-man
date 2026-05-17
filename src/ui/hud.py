"""In-game HUD overlay."""

import math
import logging

import pygame

logger = logging.getLogger(__name__)

_WHITE: tuple[int, int, int] = (255, 255, 255)
_YELLOW: tuple[int, int, int] = (255, 255, 0)
_RED: tuple[int, int, int] = (255, 60, 60)
_ORANGE: tuple[int, int, int] = (255, 165, 0)
_CHEAT_COLOR: tuple[int, int, int] = (255, 200, 0)
_FLOOR: tuple[int, int, int] = (0, 0, 0)

_font_cache: dict[int, pygame.font.Font] = {}


def _font(size: int) -> pygame.font.Font:
    if size not in _font_cache:
        _font_cache[size] = pygame.font.Font(None, size)
    return _font_cache[size]


def _draw_mini_pacman(
    screen: pygame.Surface,
    cx: int,
    cy: int,
    r: int,
) -> None:
    """Draw a tiny Pac-Man icon used to represent a life."""
    pygame.draw.circle(screen, _YELLOW, (cx, cy), r)
    pts: list[tuple[int, int]] = [(cx, cy)]
    for i in range(5):
        a = math.radians(30 + i * (300 / 4))
        pts.append((
            int(cx + (r + 1) * math.cos(a)),
            int(cy + (r + 1) * math.sin(a)),
        ))
    pygame.draw.polygon(screen, _FLOOR, pts)


class HUD:
    """Renders the in-game heads-up display."""

    def render(
        self,
        screen: pygame.Surface,
        score: int,
        lives: int,
        level: int,
        time_remaining: float,
        active_cheats: list[str],
        offset_y: int,
    ) -> None:
        """Draw score, lives, level number, timer, and active cheats.

        Args:
            screen: Pygame surface to draw on.
            score: Current player score.
            lives: Remaining lives.
            level: Current level number (1-based).
            time_remaining: Seconds left in the level.
            active_cheats: Names of active cheats to display.
            offset_y: Top-left y position for the HUD strip.
        """
        w = screen.get_width()

        # Background strip
        pygame.draw.rect(screen, (10, 10, 30), (0, offset_y, w, 48))
        pygame.draw.line(
            screen, (0, 0, 100), (0, offset_y), (w, offset_y), 1
        )

        # Score
        score_surf = _font(18).render(f"SCORE {score:>7}", True, _WHITE)
        screen.blit(score_surf, (8, offset_y + 4))

        # Level
        lvl_text = f"LEVEL {level}"
        lvl_surf = _font(18).render(lvl_text, True, _WHITE)
        screen.blit(
            lvl_surf,
            (w // 2 - lvl_surf.get_width() // 2, offset_y + 4),
        )

        # Timer (orange → red as it counts down)
        secs = int(time_remaining)
        timer_color = _RED if secs <= 10 else (
            _ORANGE if secs <= 20 else _WHITE
        )
        timer_surf = _font(18).render(f"TIME {secs:>3}s", True, timer_color)
        screen.blit(timer_surf, (w - timer_surf.get_width() - 8, offset_y + 4))

        # Lives: mini Pac-Man icons or xN text
        life_r = 7
        life_y = offset_y + 30
        if lives <= 5:
            for i in range(lives):
                _draw_mini_pacman(
                    screen, 12 + i * (life_r * 2 + 6), life_y, life_r
                )
        else:
            _draw_mini_pacman(screen, 12, life_y, life_r)
            txt = f"x{lives}"
            surf = _font(16).render(txt, True, _WHITE)
            pos = (12 + life_r + 4, life_y - surf.get_height() // 2)
            screen.blit(surf, pos)

        # Active cheats
        if active_cheats:
            cheat_text = "CHEATS: " + "  ".join(active_cheats)
            cheat_surf = _font(14).render(cheat_text, True, _CHEAT_COLOR)
            screen.blit(
                cheat_surf,
                (w - cheat_surf.get_width() - 8, offset_y + 30),
            )
