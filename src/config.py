"""Configuration loader for Pac-Man.

Parses a JSON config file (with # comment support) into validated
Pydantic models. Invalid values are clamped to safe defaults via
field validators. Invalid or unreadable config files raise a clean
ConfigLoadError for the entrypoint to report without a traceback.
"""

import json
import logging
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)

logger = logging.getLogger(__name__)

_MIN_LEVELS: int = 10
_MAX_MAZE_DIMENSION: int = 100
_MAX_SEED: int = 2**31 - 1


def _config_path(info: ValidationInfo, field_name: str | None) -> str:
    """Return a dotted config path for a validation warning."""
    context = info.context or {}
    prefix = context.get("config_path", "")
    name = field_name or "value"
    return f"{prefix}.{name}" if prefix else name


def _clamp_int(
    value: Any,
    field_name: str,
    minimum: int,
    maximum: int | None,
    default: int,
) -> int:
    """Convert and clamp an integer while logging any correction."""
    try:
        converted = int(value)
    except (TypeError, ValueError, OverflowError):
        logger.warning(
            "Config '%s' value %r is invalid, using default %d",
            field_name,
            value,
            default,
        )
        return default

    if converted < minimum:
        logger.warning(
            "Config '%s' value %r is below minimum %d, clamping to %d",
            field_name,
            value,
            minimum,
            minimum,
        )
        return minimum
    if maximum is not None and converted > maximum:
        logger.warning(
            "Config '%s' value %r is above maximum %d, clamping to %d",
            field_name,
            value,
            maximum,
            maximum,
        )
        return maximum
    return converted


def _warn_missing_fields(
    data: Any,
    info: ValidationInfo,
    defaults: dict[str, Any],
) -> Any:
    """Log defaults used for fields absent from an external config."""
    if not isinstance(data, dict) or not (info.context or {}).get(
        "log_missing"
    ):
        return data

    for field_name, default in defaults.items():
        if field_name not in data:
            logger.warning(
                "Config '%s' is missing, using default %s",
                _config_path(info, field_name),
                default,
            )
    return data


class ConfigLoadError(Exception):
    """Raised when the config file itself cannot be loaded."""


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

    width: int = Field(default=20, ge=7, le=_MAX_MAZE_DIMENSION)
    height: int = Field(default=20, ge=7, le=_MAX_MAZE_DIMENSION)
    seed: int = Field(default=42, ge=0, le=_MAX_SEED)

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def warn_missing_values(cls, data: Any, info: ValidationInfo) -> Any:
        """Warn when an external level omits configurable values."""
        defaults = {"width": 20, "height": 20}
        if (info.context or {}).get("config_path") == "levels[0]":
            defaults["seed"] = 42
        return _warn_missing_fields(
            data,
            info,
            defaults,
        )

    @field_validator("width", "height", mode="before")
    @classmethod
    def clamp_dimension(cls, v: Any, info: ValidationInfo) -> int:
        """Clamp width/height to the supported range of 7 to 100.

        Args:
            v: Raw field value.

        Returns:
            Integer clamped to valid range.
        """
        return _clamp_int(
            v,
            _config_path(info, info.field_name),
            7,
            _MAX_MAZE_DIMENSION,
            20,
        )

    @field_validator("seed", mode="before")
    @classmethod
    def clamp_seed(cls, v: Any, info: ValidationInfo) -> int:
        """Clamp seed to [0, 2^31-1].

        Args:
            v: Raw field value.

        Returns:
            Integer clamped to valid range.
        """
        return _clamp_int(
            v,
            _config_path(info, info.field_name),
            0,
            _MAX_SEED,
            42,
        )


def _default_levels() -> list[LevelConfig]:
    """Return the minimum set of independent default level configs."""
    return [LevelConfig() for _ in range(_MIN_LEVELS)]


class GameConfig(BaseModel):
    """Full validated game configuration."""

    highscore_filename: str = "highscores.json"
    lives: int = Field(default=3, ge=1, le=99)
    pacgum: int = Field(default=42, ge=1, le=9999)
    points_per_pacgum: int = Field(default=10, ge=1, le=99999)
    points_per_super_pacgum: int = Field(default=50, ge=1, le=99999)
    points_per_ghost: int = Field(default=200, ge=1, le=99999)
    level_max_time: int = Field(default=90, ge=10, le=3600)
    levels: list[LevelConfig] = Field(default_factory=_default_levels)

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def warn_missing_values(cls, data: Any, info: ValidationInfo) -> Any:
        """Warn when an external config omits configurable values."""
        data = _warn_missing_fields(
            data,
            info,
            {
                "highscore_filename": "highscores.json",
                "lives": 3,
                "pacgum": 42,
                "points_per_pacgum": 10,
                "points_per_super_pacgum": 50,
                "points_per_ghost": 200,
                "level_max_time": 90,
            },
        )
        if (
            isinstance(data, dict)
            and (info.context or {}).get("log_missing")
            and "levels" not in data
        ):
            logger.warning(
                "Config 'levels' is missing, using %d default levels",
                _MIN_LEVELS,
            )
        return data

    @field_validator("highscore_filename", mode="before")
    @classmethod
    def validate_filename(cls, v: Any, info: ValidationInfo) -> str:
        """Fall back to default if filename is blank or not a string.

        Args:
            v: Raw field value.

        Returns:
            Validated filename string.
        """
        if not isinstance(v, str) or not v.strip():
            logger.warning(
                "Config '%s' value %r is invalid, using default %r",
                _config_path(info, info.field_name),
                v,
                "highscores.json",
            )
            return "highscores.json"
        return v.strip()

    @field_validator("lives", mode="before")
    @classmethod
    def clamp_lives(cls, v: Any, info: ValidationInfo) -> int:
        """Clamp lives to [1, 99].

        Args:
            v: Raw field value.

        Returns:
            Integer clamped to valid range.
        """
        return _clamp_int(v, _config_path(info, info.field_name), 1, 99, 3)

    @field_validator("pacgum", mode="before")
    @classmethod
    def clamp_pacgum(cls, v: Any, info: ValidationInfo) -> int:
        """Clamp pacgum count to [1, 9999].

        Args:
            v: Raw field value.

        Returns:
            Integer clamped to valid range.
        """
        return _clamp_int(
            v, _config_path(info, info.field_name), 1, 9999, 42
        )

    @field_validator(
        "points_per_pacgum",
        "points_per_super_pacgum",
        "points_per_ghost",
        mode="before",
    )
    @classmethod
    def clamp_points(cls, v: Any, info: ValidationInfo) -> int:
        """Clamp point values to [1, 99999].

        Args:
            v: Raw field value.

        Returns:
            Integer clamped to valid range.
        """
        defaults = {
            "points_per_pacgum": 10,
            "points_per_super_pacgum": 50,
            "points_per_ghost": 200,
        }
        field_name = info.field_name or "points_per_pacgum"
        return _clamp_int(
            v,
            _config_path(info, field_name),
            1,
            99999,
            defaults[field_name],
        )

    @field_validator("level_max_time", mode="before")
    @classmethod
    def clamp_level_max_time(cls, v: Any, info: ValidationInfo) -> int:
        """Clamp level_max_time to [10, 3600].

        Args:
            v: Raw field value.

        Returns:
            Integer clamped to valid range.
        """
        return _clamp_int(
            v, _config_path(info, info.field_name), 10, 3600, 90
        )

    @field_validator("levels", mode="before")
    @classmethod
    def validate_levels(cls, v: Any, info: ValidationInfo) -> list[Any]:
        """Validate level entries and replace invalid items with defaults.

        Args:
            v: Raw field value.

        Returns:
            List of level dicts or LevelConfig instances.
        """
        if not isinstance(v, list) or not v:
            logger.warning(
                "Config 'levels' value %r is invalid or empty, using %d "
                "default levels",
                v,
                _MIN_LEVELS,
            )
            return [LevelConfig() for _ in range(_MIN_LEVELS)]

        levels: list[Any] = []
        for index, item in enumerate(v):
            if isinstance(item, LevelConfig):
                levels.append(item)
            elif isinstance(item, dict):
                context = dict(info.context or {})
                context["config_path"] = f"levels[{index}]"
                levels.append(
                    LevelConfig.model_validate(item, context=context)
                )
            else:
                logger.warning(
                    "Config 'levels[%d]' value %r is invalid, using "
                    "default level",
                    index,
                    item,
                )
                levels.append(LevelConfig())

        if len(levels) < _MIN_LEVELS:
            defaults_needed = _MIN_LEVELS - len(levels)
            logger.warning(
                "Config 'levels' has %d entries, adding %d default levels "
                "to reach the minimum of %d",
                len(levels),
                defaults_needed,
                _MIN_LEVELS,
            )
            levels.extend(LevelConfig() for _ in range(defaults_needed))
        return levels


def load_config(path: str) -> GameConfig:
    """Load and validate a game config file.

    Invalid values inside a readable JSON object are clamped to safe
    defaults with a log warning. Unknown keys are silently ignored.

    Args:
        path: Path to the JSON config file (# comments supported).

    Returns:
        A fully validated GameConfig instance.

    Raises:
        ConfigLoadError: If the file cannot be read, parsed, or if the
            JSON root is not an object.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw_text = fh.read()
    except OSError as exc:
        raise ConfigLoadError(
            f"Cannot open config '{path}': {exc}"
        ) from exc

    try:
        data: Any = json.loads(_strip_comments(raw_text))
    except json.JSONDecodeError as exc:
        raise ConfigLoadError(
            f"Config '{path}' is not valid JSON: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ConfigLoadError(
            f"Config '{path}' must be a JSON object"
        )

    try:
        return GameConfig.model_validate(
            data,
            context={"log_missing": True},
        )
    except ValidationError as exc:
        logger.error(
            "Config '%s' has invalid values: %s — using all defaults",
            path,
            exc,
        )
        return GameConfig(levels=[LevelConfig() for _ in range(10)])
