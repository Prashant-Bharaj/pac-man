"""Main menu screen."""

import logging

import pygame

from src.highscore import HighscoreEntry

logger = logging.getLogger(__name__)

_YELLOW: tuple[int, int, int] = (255, 255, 0)
_WHITE: tuple[int, int, int] = (255, 255, 255)
_GRAY: tuple[int, int, int] = (160, 160, 160)
_CYAN: tuple[int, int, int] = (0, 220, 220)

_font_cache: dict[int, pygame.font.Font] = {}


def _font(size: int) -> pygame.font.Font:
    if size not in _font_cache:
        _font_cache[size] = pygame.font.SysFont("monospace", size)
    return _font_cache[size]


def _blit_centred(
    screen: pygame.Surface,
    text: str,
    y: int,
    color: tuple[int, int, int],
    size: int,
) -> None:
    surf = _font(size).render(text, True, color)
    screen.blit(surf, (screen.get_width() // 2 - surf.get_width() // 2, y))


class MainMenu:
    """Renders and handles input for the main menu screen."""

    def render(
        self,
        screen: pygame.Surface,
        highscores: list[HighscoreEntry],
    ) -> None:
        """Draw the main menu with title, controls, and top scores.

        Args:
            screen: Pygame surface to draw on.
            highscores: Current top-10 entries to display.
        """
        w, h = screen.get_size()
        _blit_centred(screen, "PAC-MAN", h // 10, _YELLOW, 56)

        controls: list[tuple[str, tuple[int, int, int]]] = [
            ("SPACE  -  Start game", _WHITE),
            ("ESC    -  Quit", _WHITE),
            ("", _WHITE),
            ("Arrow keys / WASD  - Move", _GRAY),
            ("P / ESC            - Pause", _GRAY),
            ("", _GRAY),
            ("Cheats (during game):", _GRAY),
            ("  I = invincible   F = freeze ghosts", _GRAY),
            ("  S = speed boost  L = extra life   N = skip level", _GRAY),
        ]
        y = h // 4
        for text, color in controls:
            if text:
                _blit_centred(screen, text, y, color, 20)
            y += 24

        self._draw_scores(screen, h, highscores)

    def _draw_scores(
        self,
        screen: pygame.Surface,
        h: int,
        highscores: list[HighscoreEntry],
    ) -> None:
        if not highscores:
            return
        start_y = h * 1 // 2
        _blit_centred(screen, "TOP SCORES", start_y, _YELLOW, 24)
        for i, entry in enumerate(highscores[:10]):
            line = f"{i + 1:>2}. {entry.name:<10}  {entry.score:>7}"
            surf = _font(18).render(line, True, _CYAN)
            x = screen.get_width() // 2 - surf.get_width() // 2
            screen.blit(surf, (x, start_y + 34 + i * 22))

    def handle_event(self, event: object) -> str | None:
        """Process a pygame event and return the selected action.

        Args:
            event: A pygame event object.

        Returns:
            Action string ('start', 'exit') or None.
        """
        return None
