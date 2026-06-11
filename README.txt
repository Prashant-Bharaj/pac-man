==============================================================
 Pac-Man — Ghosts! More ghosts!
==============================================================

A recreation of the classic 1980 arcade Pac-Man. Navigate the
maze, eat all the pacgums, grab a super-pacgum to turn the
ghosts edible, and clear every level to win.


--------------------------------------------------------------
 REQUIREMENTS
--------------------------------------------------------------

  - Python 3.10 or later
  - uv package manager (https://docs.astral.sh/uv/)


--------------------------------------------------------------
 INSTALL & RUN
--------------------------------------------------------------

  make install        Install all dependencies into a .venv
  make run            Launch the game with the default config

  Or run directly (takes exactly one JSON config file):

      uv run python pac-man.py config.json


--------------------------------------------------------------
 CONTROLS
--------------------------------------------------------------

  In-game
    Arrow keys / WASD ... Move Pac-Man
    P / ESC ............. Pause / resume

  Pause menu
    P / ESC ............. Resume the game
    M ................... Return to the main menu

  Main menu
    UP / DOWN .......... Move selection
    ENTER / SPACE ...... Confirm
    ESC ................ Back / quit

  Game-over / Victory screen
    Type your name (max 10 letters/digits)
    ENTER .............. Save highscore and return to menu
    ESC ................ Skip and return to menu


--------------------------------------------------------------
 CHEAT KEYS (during gameplay, for review/testing)
--------------------------------------------------------------

    I .... Toggle invincibility (ghosts cannot kill you)
    F .... Toggle ghost freeze (ghosts stop moving)
    B .... Toggle speed boost (faster movement)
    L .... Add an extra life
    N .... Skip to the next level


--------------------------------------------------------------
 CONFIGURATION
--------------------------------------------------------------

  The game is launched with one argument: a JSON config file.
  Lines starting with # or // are treated as comments.

  Common keys (invalid values fall back to safe defaults):

    highscore_filename ........ Where highscores are stored
    lives ..................... Starting lives (default 3)
    points_per_pacgum ......... Score per pacgum (default 10)
    points_per_super_pacgum ... Score per super-pacgum (50)
    points_per_ghost .......... Score per eaten ghost (200)
    seed ...................... RNG seed for level 1
    level_max_time ............ Time limit per level (seconds)
    levels .................... Array of { width, height, seed }
                                (at least 10 levels)

  See config.json for a complete working example.


--------------------------------------------------------------
 GOAL
--------------------------------------------------------------

  Eat every pacgum in a maze to advance to the next level.
  Super-pacgums (in the 4 corners) make ghosts edible for a
  short time. Avoid ghosts unless they are edible. Lose all
  your lives and it's game over. Clear all levels to win.

  Waka-waka!
