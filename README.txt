==============================
 Pac-Man - Ghosts! More ghosts!
==============================

A recreation of the classic 1980 arcade Pac-Man.
Eat all the pacgums in each maze while avoiding the ghosts. Eat a
super-pacgum (corner) to make ghosts edible for a short time. Clear all
pacgums to advance; complete every level to win.


HOW TO RUN
----------
    make run

This launches the game with the default config.json. Config paths must use a
.json extension (case-insensitive). On any config error the game prints a clear
message and exits without a traceback.


CONTROLS
--------
    Arrow keys / WASD   Move Pac-Man
    P / ESC             Pause / unpause

Menus:
    UP / DOWN           Move menu selection
    ENTER / SPACE       Confirm selection
    ESC                 Back / Quit (main menu) / Main menu (pause)
    M                   Main menu (from pause)
    ENTER               Confirm name and save score (game over / victory)


CHEAT KEYS (during gameplay, for evaluation)
--------------------------------------------
    I   Toggle invincibility (ghosts cannot kill you)
    F   Toggle ghost freeze (ghosts stop moving)
    B   Toggle speed boost (faster movement)
    L   Add an extra life
    N   Skip to the next level immediately

Active cheats are shown in the HUD strip at the bottom of the screen.


CONFIGURATION
-------------
The config file is JSON and also supports comment lines starting with
'#' or '//' (stripped before parsing). All keys are optional; missing or
invalid values fall back to safe defaults without crashing.

    highscore_filename        Path to the highscore file ("highscores.json")
    lives                     Starting lives (default 3, clamped 1-99)
    points_per_pacgum         Score per pacgum (default 10, clamped 1-99999)
    points_per_super_pacgum   Score per super-pacgum (default 50, clamped
                              1-99999)
    points_per_ghost          Score per edible ghost (default 200, clamped
                              1-99999)
    level_max_time            Time limit per level, seconds (default 90,
                              clamped 10-3600)
    levels                    Array of per-level configs (width, height, and
                              seed for level 1)

The seed in the first level config generates level 1 (default 42).
Subsequent levels are generated with random seeds.

See config.json for a working example.
