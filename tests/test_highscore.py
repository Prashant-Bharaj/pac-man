"""Tests for the highscore system."""

import json
from pathlib import Path

from src.highscore import load, save, add_entry, HighscoreEntry, MAX_ENTRIES


def test_load_missing_file() -> None:
    """Loading a nonexistent file returns empty list without raising."""
    result = load("/nonexistent/highscores.json")
    assert result == []


def test_load_corrupt_file(tmp_path: Path) -> None:
    """Loading a corrupt JSON file returns empty list without raising."""
    p = tmp_path / "hs.json"
    p.write_text("not valid json")
    assert load(str(p)) == []


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    """Saved entries can be loaded back correctly."""
    p = tmp_path / "hs.json"
    entries = [HighscoreEntry(name="Alice", score=500)]
    save(str(p), entries)
    loaded = load(str(p))
    assert len(loaded) == 1
    assert loaded[0].name == "Alice"
    assert loaded[0].score == 500


def test_add_entry_keeps_top_10() -> None:
    """Adding entries beyond MAX_ENTRIES keeps only top scores."""
    entries: list[HighscoreEntry] = []
    for i in range(MAX_ENTRIES + 5):
        entries = add_entry(entries, f"P{i}", i * 10)
    assert len(entries) == MAX_ENTRIES
    assert entries[0].score == (MAX_ENTRIES + 4) * 10


def test_add_entry_sorted() -> None:
    """Entries are always sorted by score descending."""
    entries = add_entry([], "Low", 10)
    entries = add_entry(entries, "High", 1000)
    entries = add_entry(entries, "Mid", 500)
    assert entries[0].score == 1000
    assert entries[1].score == 500


def test_invalid_name_not_saved() -> None:
    """An entry with an invalid name is silently rejected."""
    entries = add_entry([], "Bad!@#Name", 100)
    assert len(entries) == 0


def test_name_too_long_truncated() -> None:
    """Names longer than 10 chars are truncated, not rejected."""
    entries = add_entry([], "VeryLongName", 100)
    assert len(entries) == 1
    assert len(entries[0].name) <= 10


def test_negative_score_clamped() -> None:
    """Negative scores are stored as zero."""
    entries = add_entry([], "Player", -50)
    assert entries[0].score == 0


def test_load_skips_invalid_entries(tmp_path: Path) -> None:
    """Invalid entries in the file are skipped without error."""
    p = tmp_path / "hs.json"
    data = [
        {"name": "Valid", "score": 100},
        {"name": "Bad!!", "score": 50},
        "not a dict",
    ]
    p.write_text(json.dumps(data))
    entries = load(str(p))
    assert len(entries) == 1
    assert entries[0].name == "Valid"
