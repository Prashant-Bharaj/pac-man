# Acceptance Test Plan

This document outlines the testing strategy, verification process, and bug-tracking for the Pac-Man project.

## 1. Testing Strategy

The project utilizes a multi-layered testing approach to ensure stability and correctness:

*   **Unit Tests:** Each core module (`src/config.py`, `src/highscore.py`, `src/entities/`, `src/maze.py`, `src/level.py`) is covered by unit tests using the `pytest` framework.
*   **Static Analysis:** Linting and type checking are integrated via `make lint`, ensuring PEP 8 compliance and early detection of potential logic errors through Mypy.
*   **Manual Evaluation:** A comprehensive cheat mode is built-in to facilitate rapid verification of high-level features during development and peer review.

## 2. Test Execution Summary

| Module | Test File | Cases | Key Features Verified |
| :--- | :--- | :--- | :--- |
| **Config** | `tests/test_config.py` | 16 | Valid JSON loading, launch errors, comment stripping, field clamping, and default fallbacks. |
| **Entrypoint** | `tests/test_entrypoint.py` | 4 | CLI argument validation and clean config-file error handling. |
| **Highscore** | `tests/test_highscore.py` | 9 | Persistent CRUD operations, name validation, top-10 sorting, and corruption recovery. |
| **Maze** | `tests/test_maze.py`, `tests/test_maze_gen.py`, `tests/test_maze_sizes.py` | 24 | Expanded grid dimensions, wall/corridor bitmask conversion, deterministic seeds, and generator smoke checks. |
| **Entities** | `tests/test_entities.py` | 35 | Player grid movement, Ghost BFS pathfinding, and Pellet state machine logic. |
| **Level** | `tests/test_level.py` | 31 | Full level update cycle, collision detection events, and level timer logic. |
| **Game Input** | `tests/test_game_input.py` | 4 | Keyboard input routing for movement, cheats, and menu actions. |
| **Menu** | `tests/test_menu.py` | 7 | Main menu navigation, highscore view, instructions view, start, and exit actions. |

**Total Tests:** 131 passing.

## 3. Manual Verification (Cheat Mode)

To verify behaviors that are harder to unit test (e.g., visual rendering, HUD accuracy, state transitions), we use the following cheat keys:

*   `I` (Invincibility): Verify that collision with ghosts does not trigger the `PLAYER_HIT` event.
*   `F` (Ghost Freeze): Verify that ghost position updates are correctly skipped in the update loop.
*   `B` (Speed Boost): Verify that Pac-Man's movement interval is reduced as expected.
*   `L` (Extra Life): Verify that life increments correctly in the HUD.
*   `N` (Next Level): Verify the smooth transition between levels and the carryover of score and lives.

## 4. Bug Tracking and Fixes

| Issue Description | Severity | Fix Summary |
| :--- | :--- | :--- |
| Ghost AI sometimes chose suboptimal paths on edge cells. | Medium | Corrected the grid bounds check in the BFS logic within `src/entities/ghost.py`. |
| Pydantic failed to clamp extremely large integers in the configuration. | Low | Added explicit `@field_validator` methods to use `min()` and `max()` for strict clamping. |
| `mazegenerator` package was missing during initial environment setup. | High | Manually installed the `.whl` package and updated the documentation to include it. |
