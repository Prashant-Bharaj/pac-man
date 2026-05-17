"""Tests for top-level gameplay input handling."""

import pygame

from src.config import GameConfig
from src.entities.player import Direction
from src.game import Game
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
