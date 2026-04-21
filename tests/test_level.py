"""Tests for Level setup, update loop, and collision logic."""

from src.cheat import CheatMode
from src.config import GameConfig
from src.level import Level, LevelEvent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cfg(**kwargs: object) -> GameConfig:
    """Return a GameConfig with one default level and optional overrides."""
    data: dict[str, object] = {
        "lives": 3,
        "level_max_time": 90,
        "points_per_pacgum": 10,
        "points_per_super_pacgum": 50,
        "points_per_ghost": 200,
        "levels": [{"width": 10, "height": 10, "seed": 1}],
    }
    data.update(kwargs)
    return GameConfig.model_validate(data)


def _level(**kwargs: object) -> Level:
    """Construct a minimal Level, forwarding kwargs to GameConfig."""
    cfg = _cfg(**kwargs)
    return Level(
        index=0,
        config=cfg,
        level_cfg=cfg.levels[0],
    )


def _no_cheat() -> CheatMode:
    return CheatMode()


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestLevelConstruction:
    def test_player_placed_on_corridor(self) -> None:
        lv = _level()
        from src.maze import is_corridor
        assert is_corridor(lv.grid, lv.player.x, lv.player.y)

    def test_ghosts_placed_at_corners(self) -> None:
        lv = _level()
        assert len(lv.ghosts) == 4

    def test_pellets_present(self) -> None:
        lv = _level()
        assert len(lv.pellets) > 0

    def test_super_pacgums_at_corners(self) -> None:
        lv = _level()
        from src.entities.pellet import PelletType
        supers = [
            p for p in lv.pellets if p.pellet_type == PelletType.SUPER_PACGUM
        ]
        assert len(supers) == 4

    def test_starting_score_propagated(self) -> None:
        cfg = _cfg()
        lv = Level(
            index=0,
            config=cfg,
            level_cfg=cfg.levels[0],
            starting_score=500,
        )
        assert lv.player.score == 500

    def test_starting_lives_propagated(self) -> None:
        cfg = _cfg()
        lv = Level(
            index=0,
            config=cfg,
            level_cfg=cfg.levels[0],
            starting_lives=5,
        )
        assert lv.player.lives == 5

    def test_default_lives_from_config(self) -> None:
        lv = _level(lives=7)
        assert lv.player.lives == 7

    def test_time_remaining_set_from_config(self) -> None:
        lv = _level(level_max_time=60)
        assert lv.time_remaining == 60.0


# ---------------------------------------------------------------------------
# Timer
# ---------------------------------------------------------------------------

class TestLevelTimer:
    def test_timer_decrements(self) -> None:
        lv = _level(level_max_time=30)
        lv.update(1.0, _no_cheat())
        assert lv.time_remaining < 30.0

    def test_timer_does_not_go_negative(self) -> None:
        lv = _level(level_max_time=10)
        lv.update(999.0, _no_cheat())
        assert lv.time_remaining == 0.0

    def test_timeout_event_when_timer_hits_zero(self) -> None:
        lv = _level(level_max_time=10)
        events = lv.update(999.0, _no_cheat())
        assert LevelEvent.TIMEOUT in events

    def test_no_movement_after_timeout(self) -> None:
        lv = _level(level_max_time=10)
        px, py = lv.player.x, lv.player.y
        lv.update(999.0, _no_cheat())
        assert lv.player.x == px and lv.player.y == py


# ---------------------------------------------------------------------------
# Pellet collisions
# ---------------------------------------------------------------------------

class TestPelletCollisions:
    def _eat_all(self, lv: Level) -> None:
        """Force-eat all pellets."""
        for p in lv.pellets:
            p.eat()

    def test_pacgum_eaten_event(self) -> None:
        lv = _level()
        from src.entities.pellet import PelletType
        normal = next(
            p for p in lv.pellets
            if p.pellet_type == PelletType.PACGUM
        )
        lv.player.x, lv.player.y = normal.x, normal.y
        events = lv.update(0.001, _no_cheat())
        assert LevelEvent.PACGUM_EATEN in events

    def test_super_pacgum_eaten_event(self) -> None:
        lv = _level()
        from src.entities.pellet import PelletType
        sup = next(
            p for p in lv.pellets if p.pellet_type == PelletType.SUPER_PACGUM
        )
        lv.player.x, lv.player.y = sup.x, sup.y
        events = lv.update(0.001, _no_cheat())
        assert LevelEvent.SUPER_PACGUM_EATEN in events

    def test_super_pacgum_makes_ghosts_edible(self) -> None:
        lv = _level()
        from src.entities.ghost import GhostState
        from src.entities.pellet import PelletType
        sup = next(
            p for p in lv.pellets if p.pellet_type == PelletType.SUPER_PACGUM
        )
        lv.player.x, lv.player.y = sup.x, sup.y
        lv.update(0.001, _no_cheat())
        # make_edible is ignored for RESPAWNING ghosts — only check active ones
        non_respawning = [
            g for g in lv.ghosts if g.state != GhostState.RESPAWNING
        ]
        assert all(g.is_edible() for g in non_respawning)

    def test_level_complete_when_all_pellets_eaten(self) -> None:
        lv = _level()
        self._eat_all(lv)
        # place player away from any ghost to avoid game-over racing
        for p in lv.pellets:
            p.eaten = False
            break  # un-eat one to avoid immediate LEVEL_COMPLETE at start
        # Re-eat that last one by standing on it
        last = next(p for p in lv.pellets if not p.eaten)
        lv.player.x, lv.player.y = last.x, last.y
        # First eat the rest
        for p in lv.pellets:
            p.eat()
        last.eaten = False
        lv.player.x, lv.player.y = last.x, last.y
        cheat = CheatMode()
        cheat.invincible = True
        cheat._refresh()
        events = lv.update(0.001, cheat)
        assert LevelEvent.LEVEL_COMPLETE in events

    def test_pellet_marked_eaten(self) -> None:
        lv = _level()
        from src.entities.pellet import PelletType
        target = next(
            p for p in lv.pellets if p.pellet_type == PelletType.PACGUM
        )
        lv.player.x, lv.player.y = target.x, target.y
        lv.update(0.001, _no_cheat())
        assert target.eaten

    def test_remaining_pacgums_decrements(self) -> None:
        lv = _level()
        before = lv.remaining_pacgums()
        from src.entities.pellet import PelletType
        target = next(
            p for p in lv.pellets if p.pellet_type == PelletType.PACGUM
        )
        lv.player.x, lv.player.y = target.x, target.y
        lv.update(0.001, _no_cheat())
        assert lv.remaining_pacgums() == before - 1


# ---------------------------------------------------------------------------
# Ghost collisions
# ---------------------------------------------------------------------------

class TestGhostCollisions:
    def _overlap_ghost(self, lv: Level) -> None:
        """Move the first active, non-edible ghost onto the player."""
        from src.entities.ghost import GhostState
        for ghost in lv.ghosts:
            if ghost.state == GhostState.CHASE:
                ghost.x, ghost.y = lv.player.x, lv.player.y
                return

    def test_player_hit_event_on_ghost_overlap(self) -> None:
        lv = _level(lives=3)
        self._overlap_ghost(lv)
        events = lv.update(0.001, _no_cheat())
        assert LevelEvent.PLAYER_HIT in events

    def test_player_loses_life_on_hit(self) -> None:
        lv = _level(lives=3)
        self._overlap_ghost(lv)
        lv.update(0.001, _no_cheat())
        assert lv.player.lives == 2

    def test_game_over_when_last_life_lost(self) -> None:
        lv = _level(lives=1)
        self._overlap_ghost(lv)
        events = lv.update(0.001, _no_cheat())
        assert LevelEvent.GAME_OVER in events

    def test_ghost_eaten_event_when_edible(self) -> None:
        lv = _level()
        ghost = lv.ghosts[0]
        ghost.make_edible()
        ghost.x, ghost.y = lv.player.x, lv.player.y
        events = lv.update(0.001, _no_cheat())
        assert LevelEvent.GHOST_EATEN in events

    def test_invincible_cheat_prevents_hit(self) -> None:
        lv = _level(lives=3)
        self._overlap_ghost(lv)
        cheat = CheatMode()
        cheat.invincible = True
        cheat._refresh()
        events = lv.update(0.001, cheat)
        assert LevelEvent.PLAYER_HIT not in events
        assert LevelEvent.GAME_OVER not in events
        assert lv.player.lives == 3


# ---------------------------------------------------------------------------
# Cheat effects
# ---------------------------------------------------------------------------

class TestCheats:
    def test_ghost_freeze_stops_movement(self) -> None:
        lv = _level()
        positions_before = [(g.x, g.y) for g in lv.ghosts]
        cheat = CheatMode()
        cheat.ghost_freeze = True
        cheat._refresh()
        # Run many ticks to ensure ghosts would normally move
        for _ in range(30):
            lv.update(0.05, cheat)
        positions_after = [(g.x, g.y) for g in lv.ghosts]
        assert positions_before == positions_after

    def test_speed_boost_sets_faster_interval(self) -> None:
        lv = _level()
        cheat = CheatMode()
        cheat.speed_boost = True
        cheat._refresh()
        lv.update(0.001, cheat)
        from src.level import SPEED_BOOST
        assert lv.player.move_interval == SPEED_BOOST

    def test_normal_speed_without_cheat(self) -> None:
        lv = _level()
        lv.update(0.001, _no_cheat())
        from src.level import SPEED_NORMAL
        assert lv.player.move_interval == SPEED_NORMAL


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

class TestLevelQueries:
    def test_is_complete_false_initially(self) -> None:
        lv = _level()
        assert not lv.is_complete()

    def test_is_complete_true_when_all_eaten(self) -> None:
        lv = _level()
        for p in lv.pellets:
            p.eat()
        assert lv.is_complete()

    def test_pellet_at_returns_uneaten(self) -> None:
        lv = _level()
        target = lv.pellets[0]
        found = lv.pellet_at(target.x, target.y)
        assert found is target

    def test_pellet_at_returns_none_after_eaten(self) -> None:
        lv = _level()
        target = lv.pellets[0]
        target.eat()
        assert lv.pellet_at(target.x, target.y) is None

    def test_pellet_at_returns_none_for_empty_cell(self) -> None:
        lv = _level()
        assert lv.pellet_at(-1, -1) is None
