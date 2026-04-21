"""Core game loop and state machine."""

import logging
from enum import Enum, auto

import pygame

from src.cheat import CheatMode
from src.config import GameConfig, LevelConfig
from src.entities.player import Direction
from src.highscore import add_entry, load, save
from src.level import Level, LevelEvent
from src.maze import CellType

logger = logging.getLogger(__name__)

TARGET_FPS: int = 60
CELL_SIZE: int = 16
HUD_HEIGHT: int = 48

_GHOST_COLORS: list[tuple[int, int, int]] = [
    (255, 0, 0),
    (255, 184, 255),
    (0, 255, 255),
    (255, 184, 82),
]


class GameState(Enum):
    """Top-level game state machine states."""

    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    NAME_ENTRY = auto()
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
        self._name_entry_buffer: str = ""
        self._highscores = load(config.highscore_filename)
        self._screen: pygame.Surface | None = None
        self._font_cache: dict[int, pygame.font.Font] = {}
        logger.info("Game initialised with %d levels", len(config.levels))

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start and run the main game loop until the player quits."""
        pygame.init()
        self._screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
        pygame.display.set_caption("Pac-Man")
        clock = pygame.time.Clock()

        while self.state != GameState.QUIT:
            dt = clock.tick(TARGET_FPS) / 1000.0
            dt = min(dt, 0.1)

            for event in pygame.event.get():
                self._handle_event(event)

            if self._screen is not None:
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
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self._enter_name_entry()
            elif key == pygame.K_ESCAPE:
                self._reset_to_menu()

        elif self.state == GameState.NAME_ENTRY:
            self._handle_name_entry_key(key)

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

    def _handle_name_entry_key(self, key: int) -> None:
        if key == pygame.K_RETURN:
            name = self._name_entry_buffer.strip() or "PLAYER"
            self._highscores = add_entry(
                self._highscores, name, self._pending_score
            )
            save(self.config.highscore_filename, self._highscores)
            self._reset_to_menu()
        elif key == pygame.K_BACKSPACE:
            self._name_entry_buffer = self._name_entry_buffer[:-1]
        elif key == pygame.K_ESCAPE:
            self._reset_to_menu()
        elif key == pygame.K_SPACE:
            if len(self._name_entry_buffer) < 10:
                self._name_entry_buffer += " "
        else:
            char = pygame.key.name(key)
            if len(char) == 1 and char.isalnum():
                if len(self._name_entry_buffer) < 10:
                    self._name_entry_buffer += char.upper()

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
        self._resize_window_for_level()
        logger.info(
            "Loaded level %d (%dx%d maze cells)",
            self.level_index + 1,
            self.level.grid_width,
            self.level.grid_height,
        )

    def _resize_window_for_level(self) -> None:
        if self.level is None or self._screen is None:
            return
        w = self.level.grid_width * CELL_SIZE
        h = self.level.grid_height * CELL_SIZE + HUD_HEIGHT
        self._screen = pygame.display.set_mode((w, h))

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
            self.state = GameState.VICTORY
        else:
            self._load_level(starting_lives=lives, starting_score=score)
            self.state = GameState.PLAYING

    def _enter_name_entry(self) -> None:
        self._name_entry_buffer = ""
        self.state = GameState.NAME_ENTRY

    def _reset_to_menu(self) -> None:
        self.level = None
        self.level_index = 0
        self.cheat = CheatMode()
        if self._screen is not None:
            self._screen = pygame.display.set_mode(
                (800, 600), pygame.RESIZABLE
            )
        self.state = GameState.MAIN_MENU

    # ------------------------------------------------------------------
    # Update / render dispatch
    # ------------------------------------------------------------------

    def _update(self, dt: float, screen: pygame.Surface) -> None:
        screen.fill((0, 0, 0))

        if self.state == GameState.MAIN_MENU:
            self._draw_main_menu(screen)
        elif self.state == GameState.PLAYING:
            self._update_playing(dt, screen)
        elif self.state == GameState.PAUSED:
            self._draw_paused(screen)
        elif self.state == GameState.GAME_OVER:
            self._draw_game_over(screen)
        elif self.state == GameState.VICTORY:
            self._draw_victory(screen)
        elif self.state == GameState.NAME_ENTRY:
            self._draw_name_entry(screen)

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
                    "Player hit — lives remaining: %d", self.level.player.lives
                )
            elif event == LevelEvent.GAME_OVER:
                self._pending_score = self.level.player.score
                self.state = GameState.GAME_OVER
                return
            elif event == LevelEvent.LEVEL_COMPLETE:
                self._advance_level()
                return
            elif event == LevelEvent.TIMEOUT:
                self._pending_score = self.level.player.score
                self.state = GameState.GAME_OVER
                return

        self._draw_level(screen)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _font(self, size: int = 24) -> pygame.font.Font:
        if size not in self._font_cache:
            self._font_cache[size] = pygame.font.SysFont("monospace", size)
        return self._font_cache[size]

    def _text(
        self,
        screen: pygame.Surface,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int] = (255, 255, 255),
        size: int = 22,
    ) -> None:
        surf = self._font(size).render(text, True, color)
        screen.blit(surf, (x, y))

    def _draw_main_menu(self, screen: pygame.Surface) -> None:
        w, h = screen.get_size()
        self._text(screen, "PAC-MAN", w // 2 - 80, h // 5, (255, 255, 0), 52)
        self._text(
            screen, "SPACE  - Start game", w // 2 - 130, h // 2 - 40
        )
        self._text(
            screen, "ESC    - Quit", w // 2 - 130, h // 2
        )
        self._text(
            screen,
            "Cheats: I=invincible  F=freeze ghosts  S=speed  L=life  N=skip",
            w // 2 - 260, h // 2 + 50,
            (160, 160, 160), 17,
        )
        if self._highscores:
            self._text(
                screen, "TOP SCORES",
                w // 2 - 70, h // 2 + 100, (255, 255, 0), 24
            )
            for i, entry in enumerate(self._highscores[:5]):
                self._text(
                    screen,
                    f"{i + 1}. {entry.name:<10}  {entry.score:>7}",
                    w // 2 - 110, h // 2 + 135 + i * 28,
                    (200, 200, 200), 20,
                )

    def _draw_level(self, screen: pygame.Surface) -> None:
        if self.level is None:
            return
        cs = CELL_SIZE

        for row in range(self.level.grid_height):
            for col in range(self.level.grid_width):
                cell = self.level.grid[row][col]
                rx, ry = col * cs, row * cs
                if cell == CellType.WALL:
                    pygame.draw.rect(screen, (0, 0, 180), (rx, ry, cs, cs))

        for pellet in self.level.pellets:
            if pellet.eaten:
                continue
            px = pellet.x * cs + cs // 2
            py = pellet.y * cs + cs // 2
            if pellet.is_super():
                pygame.draw.circle(
                    screen, (255, 200, 0), (px, py), cs // 3
                )
            else:
                pygame.draw.circle(
                    screen, (255, 200, 200), (px, py), cs // 6
                )

        for i, ghost in enumerate(self.level.ghosts):
            if not ghost.is_active():
                continue
            gx = ghost.x * cs + cs // 2
            gy = ghost.y * cs + cs // 2
            if ghost.is_edible():
                color: tuple[int, int, int] = (0, 80, 255)
            else:
                color = _GHOST_COLORS[i % len(_GHOST_COLORS)]
            pygame.draw.circle(screen, color, (gx, gy), cs // 2 - 1)

        pl = self.level.player
        pygame.draw.circle(
            screen,
            (255, 255, 0),
            (pl.x * cs + cs // 2, pl.y * cs + cs // 2),
            cs // 2 - 1,
        )

        hud_y = self.level.grid_height * cs + 4
        self._text(
            screen,
            f"Score:{pl.score:>7}  Lives:{pl.lives}  "
            f"Level:{self.level_index + 1}  "
            f"Time:{int(self.level.time_remaining):>3}s",
            4, hud_y, size=17,
        )
        if self.cheat.active_cheats:
            self._text(
                screen,
                "CHEATS: " + "  ".join(self.cheat.active_cheats),
                4, hud_y + 22,
                (255, 200, 0), 15,
            )

    def _draw_paused(self, screen: pygame.Surface) -> None:
        self._draw_level(screen)
        w, h = screen.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        self._text(
            screen, "PAUSED", w // 2 - 70, h // 2 - 50, (255, 255, 0), 44
        )
        self._text(screen, "P / ESC  - Resume", w // 2 - 110, h // 2 + 10)
        self._text(screen, "M        - Main Menu", w // 2 - 110, h // 2 + 42)

    def _draw_game_over(self, screen: pygame.Surface) -> None:
        w, h = screen.get_size()
        self._text(
            screen, "GAME OVER", w // 2 - 110, h // 3, (255, 60, 60), 46
        )
        self._text(
            screen,
            f"Score: {self._pending_score}",
            w // 2 - 80, h // 3 + 70, size=28,
        )
        self._text(
            screen, "ENTER / SPACE - Save score",
            w // 2 - 150, h // 2 + 30,
        )
        self._text(
            screen, "ESC - Main menu", w // 2 - 100, h // 2 + 65
        )

    def _draw_victory(self, screen: pygame.Surface) -> None:
        w, h = screen.get_size()
        self._text(
            screen, "VICTORY!", w // 2 - 100, h // 3, (0, 255, 100), 46
        )
        self._text(
            screen,
            f"Final Score: {self._pending_score}",
            w // 2 - 110, h // 3 + 70, size=28,
        )
        self._text(
            screen, "ENTER / SPACE - Save score",
            w // 2 - 150, h // 2 + 30,
        )
        self._text(
            screen, "ESC - Main menu", w // 2 - 100, h // 2 + 65
        )

    def _draw_name_entry(self, screen: pygame.Surface) -> None:
        w, h = screen.get_size()
        self._text(
            screen, "Enter your name:", w // 2 - 120, h // 2 - 70, size=28
        )
        self._text(
            screen,
            f"> {self._name_entry_buffer}_",
            w // 2 - 120, h // 2, (255, 255, 0), 30,
        )
        self._text(
            screen, "ENTER to confirm  ESC to cancel",
            w // 2 - 170, h // 2 + 65, (180, 180, 180), 20,
        )
