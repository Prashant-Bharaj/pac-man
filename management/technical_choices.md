# Technical Rationale

This document explains the architectural decisions and technology choices made during the development of the Pac-Man project.

## 1. Pydantic vs. Dataclasses

The project utilizes both Pydantic and Dataclasses, each chosen where they provide the most value:

| Tool | Usage Area | Rationale |
| :--- | :--- | :--- |
| **Pydantic (v2)** | Configuration loading (`src/config.py`) | Config files are external, untrusted input. Pydantic's rich validation, type coercion, and automatic clamping (via field validators) ensure the application is robust to invalid data without manual error handling. |
| **Dataclasses** | Game entities (`Player`, `Ghost`, `Pellet`) | Game entities are constructed frequently in the main loop from trusted internal data. Dataclasses provide a lightweight, high-performance alternative to Pydantic, avoiding the overhead of validation where it's not needed. |

## 2. Game State Machine

A centralized `GameState` enum and the `Game` class in `src/game.py` manage the application flow. This approach allows for:
*   **Decoupling:** Each screen (Menu, HUD, Game Over) is a separate class that only needs to know how to render based on the current state.
*   **Consistency:** The `Game` class provides a single source of truth for the active state, ensuring that transitions (e.g., from `PLAYING` to `PAUSED`) are atomic and well-defined.

## 3. Ghost AI (BFS)

Ghosts use Breadth-First Search (BFS) for pathfinding in `src/entities/ghost.py`.
*   **Why BFS?** BFS guarantees the shortest path to a target on an unweighted grid, which is perfect for Pac-Man's maze structure.
*   **Optimization:** Instead of recalculating the entire path every frame, BFS is used to determine the next immediate cell to move toward. This ensures `O(N)` memory efficiency and avoids performance bottlenecks.

## 4. Maze Expansion Logic

The logical bitmask grid provided by the `A-Maze-ing` package is expanded into a $(2H+1) \times (2W+1)$ grid of walls and corridors.
*   **Logical vs. Visual:** This expansion ensures that every "path" between cells is visually represented as a corridor, and that walls have a physical presence in the grid-based collision system.
*   **Center Placement:** Entities are placed based on these expanded coordinates, simplifying collision logic to a direct cell-by-cell comparison.

## 5. Persistent Highscore System

We chose JSON for highscore storage because it is:
*   **Portable:** Requires no external database or server.
*   **Human-Readable:** Allows for manual verification if needed.
*   **Fast:** For the top 10 scores, JSON parsing overhead is negligible.
