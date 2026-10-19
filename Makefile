install:
	poetry install

test:
	poetry run pytest

lint:
	poetry run ruff check page_loader tests

selfcheck:
	poetry check

check: selfcheck lint test

package-install:
	uv tool install dist/*.whl
