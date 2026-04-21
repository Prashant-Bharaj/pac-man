"""Ghost entity and AI state machine."""

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

EDIBLE_DURATION: float = 8.0
RESPAWN_DURATION: float = 7.0


class GhostState(Enum):
    """Ghost AI state."""

    CHASE = "chase"
    EDIBLE = "edible"
    RESPAWNING = "respawning"


@dataclass
class Ghost:
    """A single ghost entity.

    Args:
        corner_x: Home corner column.
        corner_y: Home corner row.
        ghost_id: Unique identifier (0-3).
    """

    corner_x: int
    corner_y: int
    ghost_id: int
    x: int = field(init=False)
    y: int = field(init=False)
    state: GhostState = field(init=False, default=GhostState.CHASE)
    state_timer: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        """Place ghost at its home corner."""
        self.x = self.corner_x
        self.y = self.corner_y

    def make_edible(self) -> None:
        """Transition ghost to edible state."""
        self.state = GhostState.EDIBLE
        self.state_timer = EDIBLE_DURATION
        logger.debug("Ghost %d is now edible", self.ghost_id)

    def eat(self) -> None:
        """Ghost was eaten by player; begin respawn countdown."""
        self.state = GhostState.RESPAWNING
        self.state_timer = RESPAWN_DURATION
        logger.debug(
            "Ghost %d eaten, respawning in %.1fs",
            self.ghost_id, RESPAWN_DURATION,
        )

    def respawn(self) -> None:
        """Return ghost to its home corner in CHASE state."""
        self.x = self.corner_x
        self.y = self.corner_y
        self.state = GhostState.CHASE
        self.state_timer = 0.0
        logger.debug(
            "Ghost %d respawned at corner (%d, %d)",
            self.ghost_id, self.x, self.y,
        )

    def update(self, dt: float) -> None:
        """Tick state timers and transition states.

        Args:
            dt: Delta time in seconds since last update.
        """
        if self.state in (GhostState.EDIBLE, GhostState.RESPAWNING):
            self.state_timer -= dt
            if self.state_timer <= 0:
                if self.state == GhostState.EDIBLE:
                    self.state = GhostState.CHASE
                    logger.debug("Ghost %d no longer edible", self.ghost_id)
                else:
                    self.respawn()

    def is_edible(self) -> bool:
        """Return True if this ghost can currently be eaten."""
        return self.state == GhostState.EDIBLE
