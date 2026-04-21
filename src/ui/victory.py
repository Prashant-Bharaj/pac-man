"""Victory screen with name entry — stub for Phase 6."""

import logging

logger = logging.getLogger(__name__)


class VictoryScreen:
    """Renders the victory screen and collects the player's name."""

    def render(self, score: int, name_input: str) -> None:
        """Draw victory screen with final score and name input.

        Args:
            score: Final player score.
            name_input: Current name being typed by the player.
        """
        pass

    def handle_event(self, event: object) -> str | None:
        """Process input for name entry.

        Args:
            event: A pygame event object.

        Returns:
            Confirmed player name string when Enter is pressed, else None.
        """
        return None
