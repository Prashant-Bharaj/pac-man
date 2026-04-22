"""Core game loop and state machine."""

import logging
from enum import Enum, auto

import pygame

from src.cheat import CheatMode
from src.config import GameConfig, LevelConfig
from src.entities.player import Direction
from src.highscore import add_entry, load, save
from src.level import Level, LevelEvent
from src.renderer import Renderer
from src.ui.gameover import GameOverScreen
from src.ui.hud import HUD
from src.ui.menu import MainMenu
from src.ui.pause import PauseMenu
from src.ui.victory import VictoryScreen

logger = logging.getLogger(__name__)

TARGET_FPS: int = 60
CELL_SIZE: int = 16
HUD_HEIGHT: int = 48


class GameState(Enum):
    """Top-level game state machine states."""

    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    QUIT = auto()


class Game:
    """Orchestrates the game loop and state transitions.

    Args:
        config: Validated game configuration.
    """

    def __init__(self, config: GameConfig) -> None:
        """Initialise game with given config."""
        self.config = config
        self.state = GameState.MAIN_MENU
        self.cheat = CheatMode()
        self.level_index: int = 0
        self.level: Level | None = None
        self._pending_score: int = 0
        self._name_buf: str = ""
        self._tick: int = 0
        self._highscores = load(config.highscore_filename)
        self._screen: pygame.Surface | None = None
        # UI objects — no pygame calls in __init__; safe to create here
        self._renderer = Renderer(800, 600, CELL_SIZE)
        self._menu = MainMenu()
        self._hud = HUD()
        self._pause = PauseMenu()
        self._gameover = GameOverScreen()
        self._victory = VictoryScreen()
        logger.info("Game initialised with %d levels", len(config.levels))

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start and run the main game loop until the player quits."""
        pygame.init()
        self._screen = pygame.display.set_mode(
            (800, 600), pygame.RESIZABLE
        )
        pygame.display.set_caption("Pac-Man")
        clock = pygame.time.Clock()

        while self.state != GameState.QUIT:
            dt = clock.tick(TARGET_FPS) / 1000.0
            dt = min(dt, 0.1)
            self._tick += 1

            for event in pygame.event.get():
                self._handle_event(event)

            if self._screen is not None:
                self._screen.fill((0, 0, 0))
                self._update(dt, self._screen)
                pygame.display.flip()

        pygame.quit()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def _handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.state = GameState.QUIT
            return
        if event.type == pygame.KEYDOWN:
            self._handle_keydown(event.key)

    def _handle_keydown(self, key: int) -> None:
        if self.state == GameState.MAIN_MENU:
            if key == pygame.K_SPACE:
                self._start_game()
            elif key == pygame.K_ESCAPE:
                self.state = GameState.QUIT

        elif self.state == GameState.PLAYING:
            self._handle_playing_key(key)

        elif self.state == GameState.PAUSED:
            if key in (pygame.K_p, pygame.K_ESCAPE):
                self.state = GameState.PLAYING
            elif key == pygame.K_m:
                self._reset_to_menu()

        elif self.state in (GameState.GAME_OVER, GameState.VICTORY):
            self._handle_end_screen_key(key)

    def _handle_playing_key(self, key: int) -> None:
        if self.level is None:
            return
        if key in (pygame.K_UP, pygame.K_w):
            self.level.player.set_direction(Direction.UP)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.level.player.set_direction(Direction.DOWN)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.level.player.set_direction(Direction.LEFT)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.level.player.set_direction(Direction.RIGHT)
        elif key in (pygame.K_p, pygame.K_ESCAPE):
            self.state = GameState.PAUSED
        elif key == pygame.K_i:
            self.cheat.toggle_invincible()
        elif key == pygame.K_f:
            self.cheat.toggle_ghost_freeze()
        elif key == pygame.K_s:
            self.cheat.toggle_speed_boost()
        elif key == pygame.K_l:
            self.level.player.lives += 1
            logger.debug("Cheat: extra life → %d", self.level.player.lives)
        elif key == pygame.K_n:
            self._advance_level()

    def _handle_end_screen_key(self, key: int) -> None:
        """Handle keyboard input on the game-over / victory screens."""
        if key == pygame.K_RETURN:
            name = self._name_buf.strip() or "PLAYER"
            self._highscores = add_entry(
                self._highscores, name, self._pending_score
            )
            save(self.config.highscore_filename, self._highscores)
            self._reset_to_menu()
        elif key == pygame.K_BACKSPACE:
            self._name_buf = self._name_buf[:-1]
        elif key == pygame.K_ESCAPE:
            self._reset_to_menu()
        elif key == pygame.K_SPACE:
            if len(self._name_buf) < 10:
                self._name_buf += " "
        else:
            char = pygame.key.name(key)
            if len(char) == 1 and char.isalnum():
                if len(self._name_buf) < 10:
                    self._name_buf += char.upper()

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def _start_game(self) -> None:
        self.level_index = 0
        self.cheat = CheatMode()
        self._load_level(starting_lives=0, starting_score=0)
        self.state = GameState.PLAYING

    def _load_level(
        self, starting_lives: int = 0, starting_score: int = 0
    ) -> None:
        cfg = self._level_cfg(self.level_index)
        self.level = Level(
            index=self.level_index,
            config=self.config,
            level_cfg=cfg,
            starting_lives=starting_lives,
            starting_score=starting_score,
        )
        self._resize_window()
        logger.info(
            "Loaded level %d (%dx%d cells)",
            self.level_index + 1,
            self.level.grid_width,
            self.level.grid_height,
        )

    def _resize_window(self) -> None:
        if self.level is None:
            return
        w = self.level.grid_width * CELL_SIZE
        h = self.level.grid_height * CELL_SIZE + HUD_HEIGHT
        self._screen = pygame.display.set_mode((w, h))
        self._renderer = Renderer(w, h, CELL_SIZE)

    def _level_cfg(self, index: int) -> LevelConfig:
        if index < len(self.config.levels):
            return self.config.levels[index]
        return LevelConfig()

    def _advance_level(self) -> None:
        if self.level is None:
            return
        score = self.level.player.score
        lives = self.level.player.lives
        self.level_index += 1
        if self.level_index >= len(self.config.levels):
            self._pending_score = score
            self._name_buf = ""
            self.state = GameState.VICTORY
        else:
            self._load_level(starting_lives=lives, starting_score=score)
            self.state = GameState.PLAYING

    def _reset_to_menu(self) -> None:
        self.level = None
        self.level_index = 0
        self.cheat = CheatMode()
        self._screen = pygame.display.set_mode(
            (800, 600), pygame.RESIZABLE
        )
        self._renderer = Renderer(800, 600, CELL_SIZE)
        self.state = GameState.MAIN_MENU

    # ------------------------------------------------------------------
    # Update / render dispatch
    # ------------------------------------------------------------------

    def _update(self, dt: float, screen: pygame.Surface) -> None:
        if self.state == GameState.MAIN_MENU:
            self._menu.render(screen, self._highscores)

        elif self.state == GameState.PLAYING:
            self._update_playing(dt, screen)

        elif self.state == GameState.PAUSED:
            if self.level is not None:
                self._renderer.draw_level(screen, self.level, self._tick)
                hud_y = self.level.grid_height * CELL_SIZE
                self._hud.render(
                    screen,
                    self.level.player.score,
                    self.level.player.lives,
                    self.level_index + 1,
                    self.level.time_remaining,
                    self.cheat.active_cheats,
                    hud_y,
                )
            self._pause.render(screen)

        elif self.state == GameState.GAME_OVER:
            self._gameover.render(screen, self._pending_score, self._name_buf)

        elif self.state == GameState.VICTORY:
            self._victory.render(screen, self._pending_score, self._name_buf)

    def _update_playing(self, dt: float, screen: pygame.Surface) -> None:
        if self.level is None:
            return

        events = self.level.update(dt, self.cheat)

        for event in events:
            if event == LevelEvent.PACGUM_EATEN:
                self.level.player.add_score(self.config.points_per_pacgum)
            elif event == LevelEvent.SUPER_PACGUM_EATEN:
                self.level.player.add_score(
                    self.config.points_per_super_pacgum
                )
            elif event == LevelEvent.GHOST_EATEN:
                self.level.player.add_score(self.config.points_per_ghost)
            elif event == LevelEvent.PLAYER_HIT:
                logger.info(
                    "Player hit — lives: %d", self.level.player.lives
                )
            elif event == LevelEvent.GAME_OVER:
                self._pending_score = self.level.player.score
                self._name_buf = ""
                self.state = GameState.GAME_OVER
                return
            elif event == LevelEvent.LEVEL_COMPLETE:
                self._advance_level()
                return
            elif event == LevelEvent.TIMEOUT:
                self._pending_score = self.level.player.score
                self._name_buf = ""
                self.state = GameState.GAME_OVER
                return

        self._renderer.draw_level(screen, self.level, self._tick)
        hud_y = self.level.grid_height * CELL_SIZE
        self._hud.render(
            screen,
            self.level.player.score,
            self.level.player.lives,
            self.level_index + 1,
            self.level.time_remaining,
            self.cheat.active_cheats,
            hud_y,
        )
