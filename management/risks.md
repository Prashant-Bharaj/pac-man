# Risk Analysis and Mitigation

This document identifies potential risks encountered during the Pac-Man project and the strategies implemented to mitigate them.

## Identified Risks

| Risk Category | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **External Integration** | Failure of the assigned `A-Maze-ing` package during runtime (e.g., unexpected crashes or invalid outputs). | Medium | High | **Defensive Programming:** Implemented a robust adapter in `src/maze.py` that catches common exceptions (AttributeError, ValueError, etc.) and falls back to a minimal valid "empty" maze. |
| **Performance** | Performance degradation (low FPS) during rendering or high-frequency ghost pathfinding on large mazes. | Medium | Medium | **Optimized Algorithms:** Ghost AI uses BFS only when a direction change is possible. Pygame rendering is decoupled from logic and uses efficient primitive drawing where possible. |
| **Configuration** | Invalid or corrupt configuration files provided as command-line arguments. | High | Medium | **Schema Validation:** Used Pydantic for the configuration layer to automatically validate, clamp, and provide defaults for all inputs, ensuring the game never crashes due to bad data. |
| **Persistence** | Inability to save or load highscores due to file permission issues or JSON corruption. | Low | Low | **Robust I/O:** Highscore logic in `src/highscore.py` includes error handling for all file operations and uses a "fail-safe" approach—starting fresh if the file is unreadable. |
| **Scope Creep** | Adding too many graphical features (animations, sound) and failing to meet the core functional requirements. | Medium | Medium | **Strict Phase Control:** Adhered strictly to the project roadmap. Secondary features like animated sprites were only added after the core game loop and cheat modes were verified. |

