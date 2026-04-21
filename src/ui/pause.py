"""Pause menu overlay — stub for Phase 6."""

import logging

logger = logging.getLogger(__name__)


class PauseMenu:
    """Renders and handles input for the pause menu."""

    def render(self) -> None:
        """Draw the pause overlay."""
        pass

    def handle_event(self, event: object) -> str | None:
        """Process a pygame event and return the selected action.

        Args:
            event: A pygame event object.

        Returns:
            Action string ('resume', 'main_menu') or None.
        """
        return None
