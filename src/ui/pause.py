"""Pause menu overlay."""

import logging

import pygame

logger = logging.getLogger(__name__)

_YELLOW: tuple[int, int, int] = (255, 255, 0)
_WHITE: tuple[int, int, int] = (255, 255, 255)
_GRAY: tuple[int, int, int] = (180, 180, 180)

_font_cache: dict[int, pygame.font.Font] = {}


def _font(size: int) -> pygame.font.Font:
    """Return a cached monospace font of the given size."""
    if size not in _font_cache:
        _font_cache[size] = pygame.font.SysFont("monospace", size)
    return _font_cache[size]


class PauseMenu:
    """Renders the pause menu overlay."""

    def render(self, screen: pygame.Surface) -> None:
        """Draw a semi-transparent pause overlay.

        Args:
            screen: Pygame surface to draw on (level already drawn beneath).
        """
        w, h = screen.get_size()

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        title = _font(48).render("PAUSED", True, _YELLOW)
        screen.blit(title, (w // 2 - title.get_width() // 2, h // 3))

        lines = [
            ("P / ESC  -  Resume", _WHITE),
            ("M        -  Main Menu", _GRAY),
        ]
        y = h // 3 + 70
        for text, color in lines:
            surf = _font(22).render(text, True, color)
            screen.blit(surf, (w // 2 - surf.get_width() // 2, y))
            y += 34

    def handle_event(self, event: object) -> str | None:
        """Process a pygame event and return the selected action.

        Args:
            event: A pygame event object.

        Returns:
            Action string ('resume', 'main_menu') or None.
        """
        return None
