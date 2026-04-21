"""Pygame renderer — stub for Phase 1."""

import logging

logger = logging.getLogger(__name__)


class Renderer:
    """Handles all pygame draw calls.

    Args:
        screen_width: Window width in pixels.
        screen_height: Window height in pixels.
        cell_size: Pixel size of one maze cell.
    """

    def __init__(
        self, screen_width: int, screen_height: int, cell_size: int = 24
    ) -> None:
        """Initialise renderer dimensions."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.cell_size = cell_size
        logger.debug(
            "Renderer initialised (%dx%d, cell=%d)",
            screen_width, screen_height, cell_size,
        )
