"""Tests for main menu navigation."""

import pygame

from src.ui.menu import MainMenu


def test_home_starts_on_start_game() -> None:
    """Main menu starts with Start Game selected."""
    menu = MainMenu()

    assert menu.view == "home"
    assert menu.selected_label == "Start Game"


def test_down_selects_view_highscores() -> None:
    """DOWN moves selection to View Highscores."""
    menu = MainMenu()

    menu.handle_keydown(pygame.K_DOWN)

    assert menu.selected_label == "View Highscores"


def test_view_highscores_opens_subview() -> None:
    """Activating View Highscores opens the highscore view."""
    menu = MainMenu()
    menu.handle_keydown(pygame.K_DOWN)

    action = menu.handle_keydown(pygame.K_RETURN)

    assert action is None
    assert menu.view == "highscores"


def test_escape_from_highscores_returns_home() -> None:
    """ESC from highscore view returns to the home menu."""
    menu = MainMenu()
    menu.handle_keydown(pygame.K_DOWN)
    menu.handle_keydown(pygame.K_RETURN)

    menu.handle_keydown(pygame.K_ESCAPE)

    assert menu.view == "home"
    assert menu.selected_label == "Start Game"


def test_view_instructions_opens_subview() -> None:
    """Activating Instructions opens the instructions view."""
    menu = MainMenu()
    menu.handle_keydown(pygame.K_DOWN)
    menu.handle_keydown(pygame.K_DOWN)

    action = menu.handle_keydown(pygame.K_SPACE)

    assert action is None
    assert menu.view == "instructions"


def test_start_game_returns_start_action() -> None:
    """Activating Start Game returns the start action."""
    menu = MainMenu()

    assert menu.handle_keydown(pygame.K_RETURN) == "start"


def test_exit_returns_exit_action() -> None:
    """Activating Exit returns the exit action."""
    menu = MainMenu()
    menu.handle_keydown(pygame.K_UP)

    assert menu.selected_label == "Exit"
    assert menu.handle_keydown(pygame.K_RETURN) == "exit"
