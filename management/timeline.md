# Project Timeline

This document outlines the chronological development of the Pac-Man project.

| Phase | Milestone | Duration | Contributors | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | Project Scaffold | 2 Days | msantos2, prasingh | Initialized repository, set up `uv` environment, Makefile, and linting pipeline (Flake8, Mypy). |
| **Phase 2** | Configuration System | 3 Days | msantos2 | Implemented Pydantic models for `GameConfig` and `LevelConfig`, including comment stripping and field clamping. |
| **Phase 3** | Maze Integration | 2 Days | msantos2 | Developed the adapter for the external `A-Maze-ing` package and the logic to expand bitmask grids into walkable MazeGrids. |
| **Phase 4** | Core Entities & AI | 5 Days | msantos2 | Implemented Player movement logic, Ghost BFS pathfinding, and Pellet state management. |
| **Phase 5** | Game Loop & Level Logic | 4 Days | prasingh | Created the `Level` coordination logic, collision detection systems, and the top-level `Game` state machine. |
| **Phase 6** | Renderer & UI | 6 Days | prasingh | Developed the Pygame-based Renderer, animated sprites, HUD, and all menu screens (Main, Pause, GameOver, Victory). |
| **Phase 7** | Highscore System | 3 Days | msantos2 | Implemented persistent JSON-based highscore storage with validation and top-10 sorting. |
| **Phase 8** | Cheat Mode & Polish | 2 Days | prasingh, msantos2 | Integrated all 5 cheat keys, added HUD indicators, and performed final bug fixes and performance tuning. |
| **Phase 9** | Packaging & Deployment | 1 Day | msantos2 | Created the PyInstaller specification (`pac-man.spec`) and prepared the project for deployment. |
| **Phase 10** | Project Management | 1 Day | msantos2, prasingh | Generated project management documents, finalized the README, and completed codebase documentation. |

## Progress Summary

The project followed an iterative development model. Core logic (Phases 1-4) was prioritized to ensure the "engine" was stable before layering on the graphical interface and secondary systems (Phases 5-8). Packaging and final documentation (Phases 9-10) ensured the project met all submission criteria. We successfully completed all phases within the allocated time.
