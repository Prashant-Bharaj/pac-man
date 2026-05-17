"""Tests for top-level gameplay input handling."""

import pygame
from pytest import MonkeyPatch

from src.config import GameConfig
from src.entities.player import Direction
from src.game import Game, GameState
from src.level import Level


def _game_with_level() -> Game:
    """Return a Game instance with one loaded level."""
    cfg = GameConfig.model_validate({
        "levels": [{"width": 10, "height": 10, "seed": 1}],
    })
    game = Game(cfg)
    game.level = Level(index=0, config=cfg, level_cfg=cfg.levels[0])
    return game


def test_s_key_moves_down_without_toggling_speed_boost() -> None:
    """S remains WASD down movement and does not toggle speed boost."""
    game = _game_with_level()

    game._handle_playing_key(pygame.K_s)

    assert game.level is not None
    assert game.level.player.next_direction == Direction.DOWN
    assert not game.cheat.speed_boost


def test_b_key_toggles_speed_boost() -> None:
    """B toggles the speed boost cheat."""
    game = _game_with_level()

    game._handle_playing_key(pygame.K_b)

    assert game.cheat.speed_boost


def test_enter_on_main_menu_starts_game(monkeypatch: MonkeyPatch) -> None:
    """ENTER on the default main menu selection starts the game."""
    game = _game_with_level()
    called = False

    def fake_start_game() -> None:
        nonlocal called
        called = True
        game.state = GameState.PLAYING

    monkeypatch.setattr(game, "_start_game", fake_start_game)

    game._handle_keydown(pygame.K_RETURN)

    assert called
    assert game.state == GameState.PLAYING


def test_escape_on_main_menu_quits_game() -> None:
    """ESC on main menu requests application quit."""
    game = _game_with_level()

    game._handle_keydown(pygame.K_ESCAPE)

    assert game.state == GameState.QUIT


def test_layout_expands_cells_on_large_screens() -> None:
    """Large displays increase maze cell size."""
    game = _game_with_level()

    cell_size, _, win_w, win_h = game._compute_responsive_layout(
        39, 39, 1920, 1080
    )

    assert cell_size > 16
    assert win_w <= 1920
    assert win_h <= 1080


def test_layout_shrinks_cells_for_large_levels_on_small_screens() -> None:
    """Small displays shrink maze cell size to keep content fitting."""
    game = _game_with_level()

    cell_size, _, win_w, win_h = game._compute_responsive_layout(
        199, 199, 800, 600
    )

    assert cell_size < 16
    assert win_w <= 800
    assert win_h <= 600


def test_videoresize_event_updates_playing_layout(
    monkeypatch: MonkeyPatch,
) -> None:
    """VIDEORESIZE updates the layout while gameplay is active."""
    game = _game_with_level()
    game.state = GameState.PLAYING
    called: dict[str, int] = {}

    def fake_resize_window(
        max_w: int | None = None, max_h: int | None = None
    ) -> None:
        if max_w is not None:
            called["w"] = max_w
        if max_h is not None:
            called["h"] = max_h

    monkeypatch.setattr(game, "_resize_window", fake_resize_window)

    event = pygame.event.Event(pygame.VIDEORESIZE, {"w": 1024, "h": 768})
    game._handle_event(event)

    assert called == {"w": 1024, "h": 768}
