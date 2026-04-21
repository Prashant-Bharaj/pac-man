"""Pacgum and Super-pacgum pellet entities."""

from dataclasses import dataclass
from enum import Enum


class PelletType(Enum):
    """Type of pellet."""

    PACGUM = "pacgum"
    SUPER_PACGUM = "super_pacgum"


@dataclass
class Pellet:
    """A single pellet placed in the maze.

    Args:
        x: Column position in maze grid.
        y: Row position in maze grid.
        pellet_type: Whether this is a normal or super pellet.
    """

    x: int
    y: int
    pellet_type: PelletType
    eaten: bool = False

    def eat(self) -> None:
        """Mark this pellet as eaten."""
        self.eaten = True

    def is_super(self) -> bool:
        """Return True if this is a super-pacgum."""
        return self.pellet_type == PelletType.SUPER_PACGUM
