"""Game Over screen with integrated name entry."""

import logging

import pygame

logger = logging.getLogger(__name__)

_RED: tuple[int, int, int] = (255, 60, 60)
_YELLOW: tuple[int, int, int] = (255, 255, 0)
_WHITE: tuple[int, int, int] = (255, 255, 255)
_GRAY: tuple[int, int, int] = (170, 170, 170)

_font_cache: dict[int, pygame.font.Font] = {}


def _font(size: int) -> pygame.font.Font:
    if size not in _font_cache:
        _font_cache[size] = pygame.font.Font(None, size)
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


class GameOverScreen:
    """Renders the game over screen and collects the player's name."""

    def render(
        self,
        screen: pygame.Surface,
        score: int,
        name_input: str,
    ) -> None:
        """Draw the game over screen with score and name entry field.

        Args:
            screen: Pygame surface to draw on.
            score: Final player score.
            name_input: Text currently typed by the player (max 10 chars).
        """
        w, h = screen.get_size()

        _blit_centred(screen, "GAME  OVER", h // 5, _RED, 52)
        _blit_centred(
            screen, f"Score: {score}", h // 5 + 72, _WHITE, 30
        )

        # Name entry box
        box_y = h // 2
        _blit_centred(
            screen, "Enter your name:", box_y - 36, _GRAY, 22
        )
        cursor = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
        entry_text = f"> {name_input}{cursor}"
        _blit_centred(screen, entry_text, box_y, _YELLOW, 28)

        _blit_centred(
            screen,
            "ENTER - Save score     ESC - Skip",
            h * 3 // 4,
            _GRAY,
            20,
        )

    def handle_event(self, event: object) -> str | None:
        """Process input for name entry.

        Args:
            event: A pygame event object.

        Returns:
            Confirmed player name string when Enter is pressed, else None.
        """
        return None
