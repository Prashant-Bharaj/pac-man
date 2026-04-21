"""In-game HUD overlay — stub for Phase 6."""

import logging

logger = logging.getLogger(__name__)


class HUD:
    """Renders the in-game heads-up display."""

    def render(
        self,
        score: int,
        lives: int,
        level: int,
        time_remaining: float,
        active_cheats: list[str],
    ) -> None:
        """Draw score, lives, level, timer, and active cheats.

        Args:
            score: Current player score.
            lives: Remaining lives.
            level: Current level number (1-based).
            time_remaining: Seconds left in the level.
            active_cheats: List of active cheat names to display.
        """
        pass
