.PHONY: install run debug clean lint lint-strict test package

VERSION  := "0.0.1"
PKG_NAME  = pac-man-$(VERSION)
PKG_DIR   = pkg/$(PKG_NAME)
PKG_ZIP   = pkg/$(PKG_NAME).zip

install:
	uv sync --all-groups

run:
	uv run python pac-man.py config.json

debug:
	uv run python -m pdb pac-man.py config.json

package:
	rm -rf pkg/
	mkdir -p pkg/$(PKG_NAME)
	cp pac-man.py Makefile pyproject.toml uv.lock config.json \
	   mazegenerator-2.0.1-py3-none-any.whl README.txt \
	   pkg/$(PKG_NAME)/
	cp -r src tests pkg/$(PKG_NAME)/
	find pkg/$(PKG_NAME) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find pkg/$(PKG_NAME) -name "*.pyc" -o -name "*.pyo" -delete 2>/dev/null || true
	cd pkg && python3 -m zipfile -c $(PKG_NAME).zip $(PKG_NAME)/
	rm -rf pkg/$(PKG_NAME)
	@echo "Package created: pkg/$(PKG_NAME).zip"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	rm -rf pkg/

lint:
	uv run flake8 .
	uv run mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy . --strict

test:
	uv run pytest tests/ -v
