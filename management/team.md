# Team Organization

The Pac-Man project was developed by a team of two members: `prasingh` and `msantos2`. This document details the role assignments, collaboration tools, and how project-level decisions were made.

## Team Members and Roles

| Name | Role | Core Responsibilities |
| :--- | :--- | :--- |
| **msantos2** | Systems & Logic Lead | Configuration models (Pydantic), maze integration, highscore persistence, entity AI, and deployment |
| **prasingh** | Graphics & Game Loop Lead | Game state machine (`Game` class), Pygame renderer implementation, UI screens, animation system, HUD design, and collision event system. |

## Collaboration Strategy

*   **Version Control:** Git was used to manage all source code. We utilized feature branches to isolate major components (e.g., `feature/ghost-ai`, `feature/pygame-renderer`) and merged into the main branch after peer review and linting.
*   **Code Quality:** We enforced the use of `uv` for dependency management and ran `make lint` (Flake8 and Mypy) before every merge to maintain high code standards and type safety.

## Conflict Resolution & Decision Making

Major architectural decisions, such as using Pydantic for configuration and BFS for ghost pathfinding, were made collectively after discussing pros and cons (e.g., performance vs. ease of validation). When conflicts arose, we prioritized project stability and adherence to the `subject.pdf` requirements.
