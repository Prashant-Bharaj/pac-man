PAC-MAN
=======

INSTALL
    make install

RUN
    make run
    # or directly:
    uv run python pac-man.py config.json

CONTROLS
  In-game:
    Arrow keys / WASD   Move Pac-Man
    P / ESC             Pause / unpause

  Cheat keys (during gameplay):
    I   Toggle invincibility (ghosts cannot kill you)
    F   Toggle ghost freeze
    B   Toggle speed boost
    L   Add an extra life
    N   Skip to next level

  Menus:
    UP / DOWN           Navigate menu
    ENTER / SPACE       Confirm selection
    ESC                 Back / quit

CONFIGURATION
    Pass a JSON config file as the argument:
        uv run python pac-man.py config.json

    The config path is mandatory. Missing files, invalid JSON, or
    non-object JSON roots stop launch with a clear error and no traceback.

    Inside a valid JSON object, all keys are optional and fall back to
    safe defaults.

    Key                       Default   Notes
    highscore_filename        "highscores.json"
    lives                     3         clamped 1-99
    pacgum                    42
    points_per_pacgum         10
    points_per_super_pacgum   50
    points_per_ghost          200
    seed                      42        RNG seed for level 1 maze
    level_max_time            90        seconds (clamped 10-3600)
    levels                    (10 defaults)  array of {width, height, seed}

    Comments (# or //) are allowed anywhere in the JSON file.
