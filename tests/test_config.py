"""Tests for the config loader."""

import json
from pathlib import Path

from src.config import load_config, GameConfig


def write_config(tmp_path: Path, content: str) -> str:
    """Write a config file and return its path."""
    p = tmp_path / "config.json"
    p.write_text(content)
    return str(p)


def test_valid_config(tmp_path: Path) -> None:
    """A well-formed config loads all keys correctly."""
    data = {
        "lives": 5,
        "points_per_pacgum": 20,
        "points_per_super_pacgum": 100,
        "points_per_ghost": 400,
        "seed": 7,
        "level_max_time": 60,
        "highscore_filename": "scores.json",
        "levels": [{"width": 15, "height": 15, "seed": 7}],
    }
    path = write_config(tmp_path, json.dumps(data))
    cfg = load_config(path)
    assert cfg.lives == 5
    assert cfg.points_per_pacgum == 20
    assert cfg.seed == 7
    assert cfg.highscore_filename == "scores.json"
    assert len(cfg.levels) == 1
    assert cfg.levels[0].width == 15


def test_missing_file() -> None:
    """A missing config file returns default config without raising."""
    cfg = load_config("/nonexistent/path/config.json")
    assert isinstance(cfg, GameConfig)
    assert cfg.lives == 3
    assert len(cfg.levels) == 10


def test_invalid_json(tmp_path: Path) -> None:
    """A corrupt JSON file returns default config without raising."""
    path = write_config(tmp_path, "{ this is not json }")
    cfg = load_config(path)
    assert isinstance(cfg, GameConfig)
    assert cfg.lives == 3


def test_comment_stripping(tmp_path: Path) -> None:
    """Lines starting with # are stripped before JSON parsing."""
    content = '# This is a comment\n{"lives": 4}'
    path = write_config(tmp_path, content)
    cfg = load_config(path)
    assert cfg.lives == 4


def test_unknown_keys_ignored(tmp_path: Path) -> None:
    """Unknown config keys do not cause errors."""
    data = {"lives": 2, "unknown_key_xyz": "ignore_me"}
    path = write_config(tmp_path, json.dumps(data))
    cfg = load_config(path)
    assert cfg.lives == 2


def test_invalid_lives_clamped(tmp_path: Path) -> None:
    """Out-of-range lives value is clamped to safe bounds."""
    path = write_config(tmp_path, '{"lives": -5}')
    cfg = load_config(path)
    assert cfg.lives >= 1


def test_level_dimensions_clamped_to_minimum(tmp_path: Path) -> None:
    """Level dimensions below 7 are clamped to 7."""
    path = write_config(tmp_path, '{"levels": [{"width": 6, "height": 5}]}')
    cfg = load_config(path)
    assert cfg.levels[0].width == 7
    assert cfg.levels[0].height == 7


def test_level_dimensions_allow_seven(tmp_path: Path) -> None:
    """7x7 is the minimum accepted level size."""
    path = write_config(tmp_path, '{"levels": [{"width": 7, "height": 7}]}')
    cfg = load_config(path)
    assert cfg.levels[0].width == 7
    assert cfg.levels[0].height == 7


def test_level_dimensions_have_no_maximum_clamp(tmp_path: Path) -> None:
    """Level dimensions above 100 are preserved."""
    path = write_config(
        tmp_path,
        '{"levels": [{"width": 101, "height": 250}]}',
    )
    cfg = load_config(path)
    assert cfg.levels[0].width == 101
    assert cfg.levels[0].height == 250


def test_invalid_level_dimension_uses_default(tmp_path: Path) -> None:
    """Non-numeric level dimensions fall back to defaults."""
    path = write_config(
        tmp_path,
        '{"levels": [{"width": "bad", "height": "bad"}]}',
    )
    cfg = load_config(path)
    assert cfg.levels[0].width == 20
    assert cfg.levels[0].height == 20


def test_empty_levels_uses_defaults(tmp_path: Path) -> None:
    """An empty levels array falls back to 10 default levels."""
    path = write_config(tmp_path, '{"levels": []}')
    cfg = load_config(path)
    assert len(cfg.levels) == 10


def test_invalid_level_entry_uses_default(tmp_path: Path) -> None:
    """A malformed level entry is replaced with a default level."""
    path = write_config(tmp_path, '{"levels": ["bad"]}')
    cfg = load_config(path)
    assert len(cfg.levels) == 1
    assert cfg.levels[0].width == 20
    assert cfg.levels[0].height == 20
    assert cfg.levels[0].seed == 42


def test_invalid_level_entries_preserve_length(tmp_path: Path) -> None:
    """Multiple malformed level entries become default levels."""
    path = write_config(tmp_path, '{"levels": [null, 1, []]}')
    cfg = load_config(path)
    assert len(cfg.levels) == 3
    assert all(level.width == 20 for level in cfg.levels)
    assert all(level.height == 20 for level in cfg.levels)


def test_mixed_level_entries_keep_valid_values(tmp_path: Path) -> None:
    """Valid level entries are preserved while malformed ones default."""
    path = write_config(
        tmp_path,
        '{"levels": [{"width": 15, "height": 16}, "bad"]}',
    )
    cfg = load_config(path)
    assert len(cfg.levels) == 2
    assert cfg.levels[0].width == 15
    assert cfg.levels[0].height == 16
    assert cfg.levels[1].width == 20
    assert cfg.levels[1].height == 20


def test_missing_keys_use_defaults(tmp_path: Path) -> None:
    """Config with no keys at all uses all defaults."""
    path = write_config(tmp_path, '{}')
    cfg = load_config(path)
    assert cfg.lives == 3
    assert cfg.points_per_pacgum == 10
    assert cfg.points_per_ghost == 200
