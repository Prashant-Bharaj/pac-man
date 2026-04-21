"""Configuration loader for Pac-Man.

Handles JSON config files with # comment lines, validates all keys,
clamps invalid values to safe defaults, and never raises on bad input.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LevelConfig:
    """Configuration for a single level."""

    width: int = 20
    height: int = 20
    seed: int = 42


@dataclass
class GameConfig:
    """Full validated game configuration."""

    highscore_filename: str = "highscores.json"
    lives: int = 3
    pacgum: int = 42
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    seed: int = 42
    level_max_time: int = 90
    levels: list[LevelConfig] = field(default_factory=list)


def _strip_comments(text: str) -> str:
    """Remove # and // comment lines from a JSON string.

    Args:
        text: Raw file content that may contain comments.

    Returns:
        JSON string with comment lines removed.
    """
    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped.startswith("#") and not stripped.startswith("//"):
            lines.append(line)
    return "\n".join(lines)


def _clamp_int(
    value: Any,
    minimum: int,
    maximum: int,
    default: int,
    key: str,
) -> int:
    """Validate and clamp an integer config value.

    Args:
        value: Raw value from config.
        minimum: Minimum allowed value.
        maximum: Maximum allowed value.
        default: Fallback if value is invalid.
        key: Config key name for logging.

    Returns:
        Clamped integer value.
    """
    try:
        v = int(value)
    except (TypeError, ValueError):
        logger.warning(
            "Config key '%s' is invalid, using default %d", key, default
        )
        return default
    if v < minimum or v > maximum:
        clamped = max(minimum, min(maximum, v))
        logger.warning(
            "Config key '%s' value %d out of range [%d, %d], clamping to %d",
            key, v, minimum, maximum, clamped,
        )
        return clamped
    return v


def _parse_levels(raw: Any) -> list[LevelConfig]:
    """Parse and validate the levels array from config.

    Args:
        raw: Raw levels value from config dict.

    Returns:
        List of validated LevelConfig objects.
    """
    if not isinstance(raw, list) or len(raw) == 0:
        logger.warning(
            "Config 'levels' is missing or empty, using 10 default levels"
        )
        return [LevelConfig() for _ in range(10)]

    levels: list[LevelConfig] = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            logger.warning("Level %d config is not a dict, using defaults", i)
            levels.append(LevelConfig())
            continue
        levels.append(LevelConfig(
            width=_clamp_int(
                entry.get("width", 20), 10, 100, 20, f"levels[{i}].width"
            ),
            height=_clamp_int(
                entry.get("height", 20), 10, 100, 20, f"levels[{i}].height"
            ),
            seed=_clamp_int(
                entry.get("seed", 42), 0, 2**31 - 1, 42, f"levels[{i}].seed"
            ),
        ))
    return levels


def load_config(path: str) -> GameConfig:
    """Load and validate a game config file.

    Missing or invalid values are clamped to safe defaults with a log
    warning. Unknown keys are silently ignored. Never raises on bad input.

    Args:
        path: Path to the JSON config file.

    Returns:
        A fully validated GameConfig instance.
    """
    cfg = GameConfig()

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw_text = fh.read()
    except OSError as exc:
        logger.error(
            "Cannot open config file '%s': %s — using all defaults", path, exc
        )
        cfg.levels = [LevelConfig() for _ in range(10)]
        return cfg

    try:
        data: dict[str, Any] = json.loads(_strip_comments(raw_text))
    except json.JSONDecodeError as exc:
        logger.error(
            "Config file '%s' is not valid JSON: %s — using all defaults",
            path, exc,
        )
        cfg.levels = [LevelConfig() for _ in range(10)]
        return cfg

    if not isinstance(data, dict):
        logger.error(
            "Config file '%s' must be a JSON object — using all defaults",
            path,
        )
        cfg.levels = [LevelConfig() for _ in range(10)]
        return cfg

    if "highscore_filename" in data:
        v = data["highscore_filename"]
        if isinstance(v, str) and v.strip():
            cfg.highscore_filename = v.strip()
        else:
            logger.warning(
                "Config 'highscore_filename' is invalid, using default"
            )

    cfg.lives = _clamp_int(data.get("lives", 3), 1, 99, 3, "lives")
    cfg.pacgum = _clamp_int(data.get("pacgum", 42), 1, 9999, 42, "pacgum")
    cfg.points_per_pacgum = _clamp_int(
        data.get("points_per_pacgum", 10), 0, 99999, 10, "points_per_pacgum"
    )
    cfg.points_per_super_pacgum = _clamp_int(
        data.get("points_per_super_pacgum", 50),
        0, 99999, 50, "points_per_super_pacgum",
    )
    cfg.points_per_ghost = _clamp_int(
        data.get("points_per_ghost", 200), 0, 99999, 200, "points_per_ghost"
    )
    cfg.seed = _clamp_int(
        data.get("seed", 42), 0, 2**31 - 1, 42, "seed"
    )
    cfg.level_max_time = _clamp_int(
        data.get("level_max_time", 90), 10, 3600, 90, "level_max_time"
    )
    cfg.levels = _parse_levels(data.get("levels"))

    return cfg
