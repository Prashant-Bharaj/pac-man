"""On-screen D-pad for touch / mouse control in web builds."""

import pygame
from src.entities.player import Direction

_BTN = 52          # button size in pixels
_GAP = 6           # gap between buttons
_ALPHA = 180       # button background transparency
_ARROW_COLOR = (255, 255, 255)
_BG_COLOR = (60, 60, 120, _ALPHA)

# Arrow polygon points (within a _BTN x _BTN cell, centred)
_ARROWS: dict[Direction, list[tuple[int, int]]] = {
    Direction.UP:    [(26, 8),  (44, 40), (8, 40)],
    Direction.DOWN:  [(26, 44), (8, 12),  (44, 12)],
    Direction.LEFT:  [(8, 26),  (40, 8),  (40, 44)],
    Direction.RIGHT: [(44, 26), (12, 8),  (12, 44)],
}


class TouchDpad:
    """Renders four directional buttons and maps clicks to directions."""

    def __init__(self) -> None:
        self._rects: dict[Direction, pygame.Rect] = {}

    def render(self, screen: pygame.Surface) -> None:
        w, h = screen.get_size()
        step = _BTN + _GAP
        # Centre of the d-pad cross, anchored bottom-left
        cx = step + 16
        cy = h - step - 16

        self._rects = {
            Direction.UP:    pygame.Rect(cx - _BTN // 2, cy - step, _BTN, _BTN),
            Direction.DOWN:  pygame.Rect(cx - _BTN // 2, cy + _GAP, _BTN, _BTN),
            Direction.LEFT:  pygame.Rect(cx - step, cy - _BTN // 2, _BTN, _BTN),
            Direction.RIGHT: pygame.Rect(cx + _GAP, cy - _BTN // 2, _BTN, _BTN),
        }

        for direction, rect in self._rects.items():
            btn = pygame.Surface((_BTN, _BTN), pygame.SRCALPHA)
            btn.fill(_BG_COLOR)
            pygame.draw.polygon(btn, _ARROW_COLOR, _ARROWS[direction])
            screen.blit(btn, rect.topleft)

    def direction_at(self, pos: tuple[int, int]) -> Direction | None:
        for direction, rect in self._rects.items():
            if rect.collidepoint(pos):
                return direction
        return None
