"""Main menu screen — stub for Phase 6."""

import logging

logger = logging.getLogger(__name__)


class MainMenu:
    """Renders and handles input for the main menu screen."""

    def render(self) -> None:
        """Draw the main menu."""
        pass

    def handle_event(self, event: object) -> str | None:
        """Process a pygame event and return the selected action.

        Args:
            event: A pygame event object.

        Returns:
            Action string ('start', 'highscores', 'instructions', 'exit')
            or None if no action was triggered.
        """
        return None
