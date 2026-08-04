"""Command-line entrypoint tests."""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "pac-man.py"
USAGE = "Usage: python3 pac-man.py config.json"


def run_entrypoint(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the entrypoint with arguments and capture output."""
    return subprocess.run(
        [sys.executable, str(ENTRYPOINT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_missing_config_argument_exits_with_usage() -> None:
    """Entrypoint requires exactly one config argument."""
    result = run_entrypoint()

    assert result.returncode == 1
    assert USAGE in result.stdout
    assert "Traceback" not in result.stderr


def test_extra_config_argument_exits_with_usage() -> None:
    """Entrypoint rejects more than one config argument."""
    result = run_entrypoint("config.json", "extra.json")

    assert result.returncode == 1
    assert USAGE in result.stdout
    assert "Traceback" not in result.stderr


def test_missing_config_file_exits_with_error() -> None:
    """Entrypoint exits cleanly when the config file does not exist."""
    result = run_entrypoint("missing.json")

    assert result.returncode == 1
    assert "Error: Cannot open config 'missing.json':" in result.stdout
    assert "Traceback" not in result.stderr


def test_invalid_json_config_exits_with_error(tmp_path: Path) -> None:
    """Entrypoint exits cleanly when the config file is invalid JSON."""
    bad_config = tmp_path / "bad.json"
    bad_config.write_text("{ this is not json }", encoding="utf-8")

    result = run_entrypoint(str(bad_config))

    assert result.returncode == 1
    assert f"Error: Config '{bad_config}' is not valid JSON:" in result.stdout
    assert "Traceback" not in result.stderr


def test_non_json_extension_exits_with_error(tmp_path: Path) -> None:
    """Entrypoint rejects config files with a different extension."""
    config = tmp_path / "config.txt"
    config.write_text("{}", encoding="utf-8")

    result = run_entrypoint(str(config))

    assert result.returncode == 1
    assert (
        f"Error: Config file '{config}' must have a .json extension"
        in result.stdout
    )
    assert "Traceback" not in result.stderr


def test_missing_extension_exits_before_file_access(tmp_path: Path) -> None:
    """Entrypoint checks the suffix before attempting to open a path."""
    config = tmp_path / "config"

    result = run_entrypoint(str(config))

    assert result.returncode == 1
    assert (
        f"Error: Config file '{config}' must have a .json extension"
        in result.stdout
    )
    assert "Cannot open config" not in result.stdout
    assert "Traceback" not in result.stderr


def test_json_extension_is_case_insensitive(tmp_path: Path) -> None:
    """Uppercase JSON suffixes proceed to normal content validation."""
    config = tmp_path / "bad.JSON"
    config.write_text("{ invalid json }", encoding="utf-8")

    result = run_entrypoint(str(config))

    assert result.returncode == 1
    assert f"Error: Config '{config}' is not valid JSON:" in result.stdout
    assert "must have a .json extension" not in result.stdout
    assert "Traceback" not in result.stderr
