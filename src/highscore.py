"""Persistent highscore system.

Loads and saves the top 10 highscores from/to a JSON file.
Validates all entries. Robust to missing or corrupt files.
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_ENTRIES: int = 10
MAX_NAME_LEN: int = 10
NAME_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9 ]+$")


@dataclass
class HighscoreEntry:
    """A single highscore record.

    Args:
        name: Player name (max 10 alphanumeric+space chars).
        score: Non-negative integer score.
    """

    name: str
    score: int


def _validate_name(name: str) -> str:
    """Sanitize and validate a player name.

    Args:
        name: Raw player name input.

    Returns:
        Validated name, truncated to MAX_NAME_LEN.

    Raises:
        ValueError: If the name contains invalid characters.
    """
    name = name.strip()[:MAX_NAME_LEN]
    if not name:
        raise ValueError("Player name must not be empty")
    if not NAME_PATTERN.match(name):
        raise ValueError(f"Player name '{name}' contains invalid characters")
    return name


def load(path: str) -> list[HighscoreEntry]:
    """Load highscores from a JSON file.

    Args:
        path: Path to the highscore JSON file.

    Returns:
        List of HighscoreEntry sorted by score descending (up to MAX_ENTRIES).
    """
    file = Path(path)
    if not file.exists():
        logger.info("Highscore file '%s' not found, starting fresh", path)
        return []

    try:
        with open(file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning(
            "Cannot read highscore file '%s': %s — starting fresh", path, exc
        )
        return []

    if not isinstance(data, list):
        logger.warning(
            "Highscore file '%s' has unexpected format — starting fresh", path
        )
        return []

    entries: list[HighscoreEntry] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            name = _validate_name(str(item.get("name", "")))
            score = int(item.get("score", 0))
            if score < 0:
                score = 0
            entries.append(HighscoreEntry(name=name, score=score))
        except (ValueError, TypeError) as exc:
            logger.debug("Skipping invalid highscore entry: %s", exc)

    entries.sort(key=lambda e: e.score, reverse=True)
    return entries[:MAX_ENTRIES]


def save(path: str, entries: list[HighscoreEntry]) -> None:
    """Save highscores to a JSON file.

    Args:
        path: Destination file path.
        entries: List of HighscoreEntry to persist.
    """
    data = [{"name": e.name, "score": e.score} for e in entries[:MAX_ENTRIES]]
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except OSError as exc:
        logger.error("Cannot save highscores to '%s': %s", path, exc)


def add_entry(
    entries: list[HighscoreEntry], name: str, score: int
) -> list[HighscoreEntry]:
    """Add a new entry and return the updated top-10 list.

    Args:
        entries: Existing highscore list.
        name: Raw player name (will be validated).
        score: Player's final score.

    Returns:
        Updated list sorted by score descending, capped at MAX_ENTRIES.
    """
    try:
        validated_name = _validate_name(name)
    except ValueError as exc:
        logger.warning("Invalid player name: %s — score not saved", exc)
        return entries

    new_entry = HighscoreEntry(name=validated_name, score=max(0, score))
    updated = entries + [new_entry]
    updated.sort(key=lambda e: e.score, reverse=True)
    return updated[:MAX_ENTRIES]
