"""Configuration loader for Pac-Man.

Parses a JSON config file (with # comment support) into validated
Pydantic models. Invalid values are clamped to safe defaults via
field validators. Never raises on bad input.
"""

import json
import logging
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


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


class LevelConfig(BaseModel):
    """Configuration for a single level."""

    width: int = Field(default=20, ge=10, le=100)
    height: int = Field(default=20, ge=10, le=100)
    seed: int = Field(default=42, ge=0, le=2**31 - 1)

    model_config = {"extra": "ignore"}

    @field_validator("width", "height", mode="before")
    @classmethod
    def clamp_dimension(cls, v: Any) -> int:
        """Clamp width/height to [10, 100].

        Args:
            v: Raw field value.

        Returns:
            Integer clamped to valid range.
        """
        try:
            return max(10, min(100, int(v)))
        except (TypeError, ValueError):
            return 20

    @field_validator("seed", mode="before")
    @classmethod
    def clamp_seed(cls, v: Any) -> int:
        """Clamp seed to [0, 2^31-1].

        Args:
            v: Raw field value.

        Returns:
            Integer clamped to valid range.
        """
        try:
            return max(0, min(2**31 - 1, int(v)))
        except (TypeError, ValueError):
            return 42


class GameConfig(BaseModel):
    """Full validated game configuration."""

    highscore_filename: str = "highscores.json"
    lives: int = Field(default=3, ge=1, le=99)
    pacgum: int = Field(default=42, ge=1, le=9999)
    points_per_pacgum: int = Field(default=10, ge=0, le=99999)
    points_per_super_pacgum: int = Field(default=50, ge=0, le=99999)
    points_per_ghost: int = Field(default=200, ge=0, le=99999)
    seed: int = Field(default=42, ge=0, le=2**31 - 1)
    level_max_time: int = Field(default=90, ge=10, le=3600)
    levels: list[LevelConfig] = Field(default_factory=list)

    model_config = {"extra": "ignore"}

    @field_validator("highscore_filename", mode="before")
    @classmethod
    def validate_filename(cls, v: Any) -> str:
        """Fall back to default if filename is blank or not a string.

        Args:
            v: Raw field value.

        Returns:
            Validated filename string.
        """
        if not isinstance(v, str) or not v.strip():
            logger.warning(
                "Config 'highscore_filename' is invalid, using default"
            )
            return "highscores.json"
        return v.strip()

    @field_validator("lives", mode="before")
    @classmethod
    def clamp_lives(cls, v: Any) -> int:
        """Clamp lives to [1, 99].

        Args:
            v: Raw field value.

        Returns:
            Integer clamped to valid range.
        """
        try:
            return max(1, min(99, int(v)))
        except (TypeError, ValueError):
            return 3

    @field_validator("pacgum", mode="before")
    @classmethod
    def clamp_pacgum(cls, v: Any) -> int:
        """Clamp pacgum count to [1, 9999].

        Args:
            v: Raw field value.

        Returns:
            Integer clamped to valid range.
        """
        try:
            return max(1, min(9999, int(v)))
        except (TypeError, ValueError):
            return 42

    @field_validator(
        "points_per_pacgum",
        "points_per_super_pacgum",
        "points_per_ghost",
        mode="before",
    )
    @classmethod
    def clamp_points(cls, v: Any) -> int:
        """Clamp point values to [0, 99999].

        Args:
            v: Raw field value.

        Returns:
            Integer clamped to valid range.
        """
        try:
            return max(0, min(99999, int(v)))
        except (TypeError, ValueError):
            return 0

    @field_validator("seed", mode="before")
    @classmethod
    def clamp_seed(cls, v: Any) -> int:
        """Clamp seed to [0, 2^31-1].

        Args:
            v: Raw field value.

        Returns:
            Integer clamped to valid range.
        """
        try:
            return max(0, min(2**31 - 1, int(v)))
        except (TypeError, ValueError):
            return 42

    @field_validator("level_max_time", mode="before")
    @classmethod
    def clamp_level_max_time(cls, v: Any) -> int:
        """Clamp level_max_time to [10, 3600].

        Args:
            v: Raw field value.

        Returns:
            Integer clamped to valid range.
        """
        try:
            return max(10, min(3600, int(v)))
        except (TypeError, ValueError):
            return 90

    @field_validator("levels", mode="before")
    @classmethod
    def validate_levels(cls, v: Any) -> list[Any]:
        """Fall back to 10 default levels if array is missing or empty.

        Args:
            v: Raw field value.

        Returns:
            List of level dicts (may be empty list for default handling).
        """
        if not isinstance(v, list) or len(v) == 0:
            logger.warning(
                "Config 'levels' is missing or empty, using 10 default levels"
            )
            return [{}] * 10
        return v

    @model_validator(mode="after")
    def ensure_levels(self) -> "GameConfig":
        """Guarantee at least 10 levels exist after full model construction.

        Returns:
            Self with levels list padded to minimum 10 entries.
        """
        if len(self.levels) == 0:
            self.levels = [LevelConfig() for _ in range(10)]
        return self


def load_config(path: str) -> GameConfig:
    """Load and validate a game config file.

    Invalid values are clamped to safe defaults with a log warning.
    Unknown keys are silently ignored. Never raises on bad input.

    Args:
        path: Path to the JSON config file (# comments supported).

    Returns:
        A fully validated GameConfig instance.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw_text = fh.read()
    except OSError as exc:
        logger.error(
            "Cannot open config '%s': %s — using all defaults", path, exc
        )
        return GameConfig(levels=[LevelConfig() for _ in range(10)])

    try:
        data: Any = json.loads(_strip_comments(raw_text))
    except json.JSONDecodeError as exc:
        logger.error(
            "Config '%s' is not valid JSON: %s — using all defaults", path, exc
        )
        return GameConfig(levels=[LevelConfig() for _ in range(10)])

    if not isinstance(data, dict):
        logger.error(
            "Config '%s' must be a JSON object — using all defaults", path
        )
        return GameConfig(levels=[LevelConfig() for _ in range(10)])

    return GameConfig.model_validate(data)
