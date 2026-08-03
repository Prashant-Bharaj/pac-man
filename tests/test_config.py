"""Tests for the config loader."""

import json
import logging
from pathlib import Path

import pytest

from src.config import ConfigLoadError, GameConfig, LevelConfig, load_config


def write_config(tmp_path: Path, content: str) -> str:
    """Write a config file and return its path."""
    p = tmp_path / "config.json"
    p.write_text(content)
    return str(p)


def complete_config() -> dict[str, object]:
    """Return a complete valid config that requires no corrections."""
    levels = [
        {"width": 20, "height": 20, "seed": index}
        for index in range(10)
    ]
    return {
        "highscore_filename": "highscores.json",
        "lives": 3,
        "pacgum": 42,
        "points_per_pacgum": 10,
        "points_per_super_pacgum": 50,
        "points_per_ghost": 200,
        "level_max_time": 90,
        "levels": levels,
    }


def test_valid_config(tmp_path: Path) -> None:
    """A well-formed config loads all keys correctly."""
    data = {
        "lives": 5,
        "points_per_pacgum": 20,
        "points_per_super_pacgum": 100,
        "points_per_ghost": 400,
        "level_max_time": 60,
        "highscore_filename": "scores.json",
        "levels": [{"width": 15, "height": 15, "seed": 7}],
    }
    path = write_config(tmp_path, json.dumps(data))
    cfg = load_config(path)
    assert cfg.lives == 5
    assert cfg.points_per_pacgum == 20
    assert cfg.highscore_filename == "scores.json"
    assert len(cfg.levels) == 10
    assert cfg.levels[0].width == 15
    assert all(level.width == 20 for level in cfg.levels[1:])


def test_missing_file() -> None:
    """A missing config file raises a clean load error."""
    with pytest.raises(ConfigLoadError, match="Cannot open config"):
        load_config("/nonexistent/path/config.json")


def test_invalid_json(tmp_path: Path) -> None:
    """A corrupt JSON file raises a clean load error."""
    path = write_config(tmp_path, "{ this is not json }")
    with pytest.raises(ConfigLoadError, match="is not valid JSON"):
        load_config(path)


def test_json_root_must_be_object(tmp_path: Path) -> None:
    """A config file must contain a JSON object at the root."""
    path = write_config(tmp_path, "[]")
    with pytest.raises(ConfigLoadError, match="must be a JSON object"):
        load_config(path)


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
    assert len(cfg.levels) == 10
    assert cfg.levels[0].width == 20
    assert cfg.levels[0].height == 20
    assert cfg.levels[0].seed == 42


def test_invalid_level_entries_are_padded(tmp_path: Path) -> None:
    """Malformed entries keep their positions before appended defaults."""
    path = write_config(tmp_path, '{"levels": [null, 1, []]}')
    cfg = load_config(path)
    assert len(cfg.levels) == 10
    assert all(level.width == 20 for level in cfg.levels)
    assert all(level.height == 20 for level in cfg.levels)


def test_mixed_level_entries_keep_valid_values(tmp_path: Path) -> None:
    """Valid and malformed entries are preserved before padding."""
    path = write_config(
        tmp_path,
        '{"levels": [{"width": 15, "height": 16}, "bad"]}',
    )
    cfg = load_config(path)
    assert len(cfg.levels) == 10
    assert cfg.levels[0].width == 15
    assert cfg.levels[0].height == 16
    assert cfg.levels[1].width == 20
    assert cfg.levels[1].height == 20


def test_exactly_ten_levels_are_not_extended(tmp_path: Path) -> None:
    """A ten-level configuration remains exactly ten levels long."""
    levels = [{"width": 10 + index, "height": 10 + index}
              for index in range(10)]
    path = write_config(tmp_path, json.dumps({"levels": levels}))

    cfg = load_config(path)

    assert len(cfg.levels) == 10
    assert [level.width for level in cfg.levels] == list(range(10, 20))


def test_more_than_ten_levels_are_preserved(tmp_path: Path) -> None:
    """Configurations with more than ten levels are not truncated."""
    levels = [{"width": 20, "height": 20} for _ in range(12)]
    path = write_config(tmp_path, json.dumps({"levels": levels}))

    cfg = load_config(path)

    assert len(cfg.levels) == 12


def test_short_level_list_logs_padding_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Padding a short level list emits one clear warning."""
    path = write_config(tmp_path, '{"levels": [{"width": 15}]}')

    with caplog.at_level(logging.WARNING):
        cfg = load_config(path)

    assert len(cfg.levels) == 10
    assert "has 1 entries, adding 9 default levels" in caplog.text


def test_missing_keys_use_defaults(tmp_path: Path) -> None:
    """Config with no keys at all uses all defaults."""
    path = write_config(tmp_path, '{}')
    cfg = load_config(path)
    assert cfg.lives == 3
    assert cfg.points_per_pacgum == 10
    assert cfg.points_per_ghost == 200
    assert len(cfg.levels) == 10


def test_missing_keys_log_defaults(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Missing top-level and level fields identify their defaults."""
    data = complete_config()
    del data["lives"]
    levels = data["levels"]
    assert isinstance(levels, list)
    first_level = levels[0]
    assert isinstance(first_level, dict)
    del first_level["seed"]
    path = write_config(tmp_path, json.dumps(data))

    with caplog.at_level(logging.WARNING):
        cfg = load_config(path)

    assert cfg.lives == 3
    assert cfg.levels[0].seed == 42
    assert "Config 'lives' is missing, using default 3" in caplog.text
    assert (
        "Config 'levels[0].seed' is missing, using default 42"
        in caplog.text
    )


def test_missing_levels_logs_default_count(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A missing level list reports the number of generated defaults."""
    data = complete_config()
    del data["levels"]
    path = write_config(tmp_path, json.dumps(data))

    with caplog.at_level(logging.WARNING):
        cfg = load_config(path)

    assert len(cfg.levels) == 10
    assert (
        "Config 'levels' is missing, using 10 default levels"
        in caplog.text
    )


def test_later_level_seed_is_optional(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Later random levels do not require an unused seed value."""
    data = complete_config()
    levels = data["levels"]
    assert isinstance(levels, list)
    second_level = levels[1]
    assert isinstance(second_level, dict)
    del second_level["seed"]
    path = write_config(tmp_path, json.dumps(data))

    with caplog.at_level(logging.WARNING):
        cfg = load_config(path)

    assert cfg.levels[1].seed == 42
    assert not caplog.records


def test_invalid_values_log_fallbacks(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Invalid values identify their fields, values, and fallbacks."""
    data = complete_config()
    data["highscore_filename"] = None
    data["lives"] = "bad"
    data["points_per_ghost"] = []
    levels = data["levels"]
    assert isinstance(levels, list)
    first_level = levels[0]
    assert isinstance(first_level, dict)
    first_level["width"] = "wide"
    path = write_config(tmp_path, json.dumps(data))

    with caplog.at_level(logging.WARNING):
        cfg = load_config(path)

    assert cfg.highscore_filename == "highscores.json"
    assert cfg.lives == 3
    assert cfg.points_per_ghost == 0
    assert cfg.levels[0].width == 20
    assert (
        "Config 'lives' value 'bad' is invalid, using default 3"
        in caplog.text
    )
    assert (
        "Config 'points_per_ghost' value [] is invalid, using default 0"
        in caplog.text
    )
    assert (
        "Config 'levels[0].width' value 'wide' is invalid, using default 20"
        in caplog.text
    )


def test_out_of_range_values_log_clamps(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Out-of-range numeric values report their applied boundaries."""
    data = complete_config()
    data.update(
        {
            "lives": -5,
            "pacgum": 10000,
            "points_per_pacgum": -1,
            "points_per_super_pacgum": 100000,
            "points_per_ghost": -2,
            "level_max_time": 5,
        }
    )
    levels = data["levels"]
    assert isinstance(levels, list)
    first_level = levels[0]
    assert isinstance(first_level, dict)
    first_level.update({"width": 6, "height": 5, "seed": 2**31})
    second_level = levels[1]
    assert isinstance(second_level, dict)
    second_level["seed"] = -1
    path = write_config(tmp_path, json.dumps(data))

    with caplog.at_level(logging.WARNING):
        cfg = load_config(path)

    assert cfg.lives == 1
    assert cfg.pacgum == 9999
    assert cfg.points_per_pacgum == 0
    assert cfg.points_per_super_pacgum == 99999
    assert cfg.points_per_ghost == 0
    assert cfg.level_max_time == 10
    assert cfg.levels[0].width == 7
    assert cfg.levels[0].height == 7
    assert cfg.levels[0].seed == 2**31 - 1
    assert cfg.levels[1].seed == 0
    assert (
        "Config 'lives' value -5 is below minimum 1, clamping to 1"
        in caplog.text
    )
    assert (
        "Config 'pacgum' value 10000 is above maximum 9999, "
        "clamping to 9999" in caplog.text
    )
    assert (
        "Config 'levels[0].width' value 6 is below minimum 7, "
        "clamping to 7" in caplog.text
    )
    assert (
        "Config 'levels[0].seed' value 2147483648 is above maximum "
        "2147483647, clamping to 2147483647" in caplog.text
    )


def test_valid_values_and_unknown_keys_do_not_warn(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Valid coercions and ignored unknown keys produce no warnings."""
    data = complete_config()
    data["lives"] = "3"
    data["unknown_key_xyz"] = "ignore_me"
    path = write_config(tmp_path, json.dumps(data))

    with caplog.at_level(logging.WARNING):
        cfg = load_config(path)

    assert cfg.lives == 3
    assert not caplog.records


def test_direct_model_defaults_do_not_warn(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Internal model construction keeps omitted defaults quiet."""
    with caplog.at_level(logging.WARNING):
        game_config = GameConfig()
        level_config = LevelConfig()

    assert len(game_config.levels) == 10
    assert level_config.width == 20
    assert not caplog.records
