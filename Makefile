.PHONY: install run debug clean lint lint-strict test dist

# All project source files
SRC = main.py \
      src/__init__.py \
      src/config.py \
      src/game.py \
      src/level.py \
      src/maze.py \
      src/renderer.py \
      src/cheat.py \
      src/highscore.py \
      src/entities/__init__.py \
      src/entities/player.py \
      src/entities/ghost.py \
      src/entities/pellet.py \
      src/ui/__init__.py \
      src/ui/menu.py \
      src/ui/hud.py \
      src/ui/pause.py \
      src/ui/gameover.py \
      src/ui/victory.py \
      tests/__init__.py \
      tests/test_config.py \
      tests/test_highscore.py \
      tests/test_game_input.py \
      tests/test_menu.py \
      tests/test_maze.py \
      tests/test_entities.py \
      tests/test_level.py

install:
	uv sync --all-groups

run:
	uv run python main.py config.json

debug:
	uv run python -m pdb main.py config.json

dist:
	uv run pyinstaller pac-man.spec

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true

lint:
	uv run flake8 $(SRC)
	uv run mypy $(SRC) --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	uv run flake8 $(SRC)
	uv run mypy $(SRC) --strict

test:
	uv run pytest tests/ -v
