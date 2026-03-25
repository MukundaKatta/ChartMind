.PHONY: install install-dev test lint format typecheck clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	MPLBACKEND=Agg pytest tests/ -v --tb=short

test-cov:
	MPLBACKEND=Agg pytest tests/ -v --tb=short --cov=chartmind --cov-report=html

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/chartmind/

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info .pytest_cache .mypy_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
