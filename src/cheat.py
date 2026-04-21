"""Cheat mode handler for peer review purposes."""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CheatMode:
    """Tracks which cheat features are currently active."""

    invincible: bool = False
    ghost_freeze: bool = False
    speed_boost: bool = False
    active_cheats: list[str] = field(init=False, default_factory=list)

    def _refresh(self) -> None:
        """Rebuild the active cheat name list for HUD display."""
        names = []
        if self.invincible:
            names.append("INVINCIBLE")
        if self.ghost_freeze:
            names.append("FREEZE")
        if self.speed_boost:
            names.append("SPEED")
        self.active_cheats = names

    def toggle_invincible(self) -> None:
        """Toggle player invincibility."""
        self.invincible = not self.invincible
        logger.debug("Invincibility: %s", self.invincible)
        self._refresh()

    def toggle_ghost_freeze(self) -> None:
        """Toggle ghost movement freeze."""
        self.ghost_freeze = not self.ghost_freeze
        logger.debug("Ghost freeze: %s", self.ghost_freeze)
        self._refresh()

    def toggle_speed_boost(self) -> None:
        """Toggle player speed boost."""
        self.speed_boost = not self.speed_boost
        logger.debug("Speed boost: %s", self.speed_boost)
        self._refresh()

    def is_any_active(self) -> bool:
        """Return True if any cheat is currently enabled."""
        return bool(self.active_cheats)
