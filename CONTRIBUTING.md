# Contributing to ChartMind

Thank you for your interest in contributing to ChartMind! This guide will help you get started.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/officethree/ChartMind.git
cd ChartMind

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install in development mode with dev dependencies
make install-dev
```

## Running Tests

```bash
make test

# With coverage report
make test-cov
```

## Code Quality

```bash
# Lint
make lint

# Type checking
make typecheck

# Auto-format
make format
```

## Pull Request Process

1. Fork the repository and create a feature branch from `main`.
2. Write tests for any new functionality.
3. Ensure all tests pass and linting is clean.
4. Update documentation if you change public APIs.
5. Open a pull request with a clear description of the change.

## Coding Standards

- Python 3.9+ syntax.
- Follow PEP 8 (enforced by `ruff`).
- Type hints on all public functions.
- Docstrings on all public classes and methods.

## Reporting Issues

Open an issue on GitHub with:
- A clear title and description.
- Steps to reproduce (if it is a bug).
- Expected vs. actual behaviour.
- Python version and OS.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
