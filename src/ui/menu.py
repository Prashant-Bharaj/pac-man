"""Main menu screen."""

import logging
from dataclasses import dataclass
from typing import Literal

import pygame

from src.highscore import HighscoreEntry

logger = logging.getLogger(__name__)

_YELLOW: tuple[int, int, int] = (255, 255, 0)
_WHITE: tuple[int, int, int] = (255, 255, 255)
_GRAY: tuple[int, int, int] = (160, 160, 160)
_CYAN: tuple[int, int, int] = (0, 220, 220)
_BLACK: tuple[int, int, int] = (0, 0, 0)
_PANEL: tuple[int, int, int] = (8, 8, 28)
_BLUE: tuple[int, int, int] = (20, 20, 120)
_DARK_BLUE: tuple[int, int, int] = (0, 0, 70)

MenuView = Literal["home", "highscores", "instructions"]
MenuAction = Literal["start", "exit"]
MenuItemAction = Literal["start", "highscores", "instructions", "exit"]


@dataclass(frozen=True)
class MenuItem:
    """A selectable menu item."""

    label: str
    action: MenuItemAction


_font_cache: dict[int, pygame.font.Font] = {}


def _font(size: int) -> pygame.font.Font:
    """Return a cached monospace font of the given size."""
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
    """Render text and blit it horizontally centred at y."""
    surf = _font(size).render(text, True, color)
    screen.blit(surf, (screen.get_width() // 2 - surf.get_width() // 2, y))


class MainMenu:
    """Renders and handles input for the main menu screen."""

    def __init__(self) -> None:
        """Initialise menu navigation state."""
        self.view: MenuView = "home"
        self.selected_index: int = 0
        self._items: list[MenuItem] = [
            MenuItem("Start Game", "start"),
            MenuItem("View Highscores", "highscores"),
            MenuItem("Instructions", "instructions"),
            MenuItem("Exit", "exit"),
        ]

    def render(
        self,
        screen: pygame.Surface,
        highscores: list[HighscoreEntry],
    ) -> None:
        """Draw the current menu view.

        Args:
            screen: Pygame surface to draw on.
            highscores: Current top-10 entries to display.
        """
        screen.fill(_BLACK)
        w, h = screen.get_size()
        _blit_centred(screen, "PAC-MAN", h // 11, _YELLOW, 56)
        _blit_centred(
            screen, "Ghosts! More ghosts!", h // 11 + 58, _CYAN, 18
        )

        if self.view == "home":
            self._draw_home(screen, w, h)
        elif self.view == "highscores":
            self._draw_highscores(screen, w, h, highscores)
        else:
            self._draw_instructions(screen, w, h)

        _blit_centred(
            screen,
            "UP/DOWN - Select    ENTER/SPACE - Confirm    ESC - Back/Quit",
            h - 36,
            _GRAY,
            16,
        )

    def handle_keydown(self, key: int) -> MenuAction | None:
        """Handle keyboard input and return a game-level action if any.

        Args:
            key: Pygame key constant.

        Returns:
            "start", "exit", or None when the menu consumes the key.
        """
        if self.view != "home":
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.view = "home"
                self.selected_index = 0
            return None

        if key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(self._items)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self._items)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            return self._activate_selected()
        elif key == pygame.K_ESCAPE:
            return "exit"
        return None

    @property
    def selected_label(self) -> str:
        """Return the currently selected home menu label."""
        return self._items[self.selected_index].label

    def _activate_selected(self) -> MenuAction | None:
        """Activate the current home menu selection."""
        item = self._items[self.selected_index]
        if item.action == "start":
            return "start"
        if item.action == "exit":
            return "exit"
        if item.action in ("highscores", "instructions"):
            self.view = item.action
            self.selected_index = 0
        return None

    def _draw_home(self, screen: pygame.Surface, w: int, h: int) -> None:
        """Draw the menu items with the selection highlighted."""
        start_y = h // 3
        item_w = min(360, w - 80)
        item_h = 46
        gap = 14
        x = w // 2 - item_w // 2

        for i, item in enumerate(self._items):
            y = start_y + i * (item_h + gap)
            selected = i == self.selected_index
            fill = _BLUE if selected else _PANEL
            border = _YELLOW if selected else _DARK_BLUE
            rect = (x, y, item_w, item_h)
            pygame.draw.rect(screen, fill, rect, border_radius=6)
            pygame.draw.rect(
                screen, border, rect, width=2, border_radius=6
            )
            color = _YELLOW if selected else _WHITE
            _blit_centred(screen, item.label.upper(), y + 12, color, 22)

    def _draw_highscores(
        self,
        screen: pygame.Surface,
        w: int,
        h: int,
        highscores: list[HighscoreEntry],
    ) -> None:
        """Draw the top-10 highscores list."""
        _blit_centred(screen, "TOP 10 HIGHSCORES", h // 4, _YELLOW, 28)
        if not highscores:
            _blit_centred(screen, "No scores yet", h // 4 + 56, _GRAY, 22)
        else:
            y = h // 4 + 48
            for i, entry in enumerate(highscores[:10]):
                line = f"{i + 1:>2}. {entry.name:<10} {entry.score:>7}"
                surf = _font(20).render(line, True, _CYAN)
                screen.blit(surf, (w // 2 - surf.get_width() // 2, y))
                y += 26
        _blit_centred(
            screen, "ENTER / SPACE / ESC - Back", h - 76, _WHITE, 18
        )

    def _draw_instructions(
        self, screen: pygame.Surface, w: int, h: int
    ) -> None:
        """Draw the controls and rules screen."""
        _blit_centred(screen, "INSTRUCTIONS", h // 4, _YELLOW, 28)
        lines = [
            "Move: Arrow keys or WASD",
            "Pause: P or ESC",
            "Eat all pacgums to clear each level",
            "Super-pacgums make ghosts edible for a short time",
            "Cheats: I invincible, F freeze, B speed, L life, N next level",
        ]
        y = h // 4 + 54
        for line in lines:
            surf = _font(19).render(line, True, _WHITE)
            screen.blit(surf, (w // 2 - surf.get_width() // 2, y))
            y += 32
        _blit_centred(
            screen, "ENTER / SPACE / ESC - Back", h - 76, _WHITE, 18
        )
