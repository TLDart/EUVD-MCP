.PHONY: help install dev test lint format security docker clean

# Variables
PYTHON := python3
POETRY := poetry
DOCKER := docker
COMPOSE := docker-compose

help:
	@echo "EUVD-MCP Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies"
	@echo "  make dev              Install dev dependencies"
	@echo "  make pre-commit-setup Install pre-commit hooks"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run all linters"
	@echo "  make format           Format code with Black and isort"
	@echo "  make test             Run tests"
	@echo "  make coverage         Generate coverage report"
	@echo "  make pre-commit       Run pre-commit checks on all files"
	@echo ""
	@echo "Security:"
	@echo "  make security         Run security checks"
	@echo "  make audit            Audit dependencies"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-run       Run Docker container"
	@echo "  make compose-up       Start with docker-compose"
	@echo "  make compose-down     Stop docker-compose"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts"
	@echo "  make clean-all        Remove all artifacts including venv"

install:
	@echo "Installing dependencies..."
	$(POETRY) install

dev:
	@echo "Installing dev dependencies..."
	$(POETRY) install
	$(POETRY) add --group dev flake8 mypy black isort pytest pytest-cov pylint ruff bandit safety pip-audit pre-commit pydocstyle

pre-commit-setup:
	@echo "Setting up pre-commit hooks..."
	$(POETRY) run pre-commit install
	@echo "Pre-commit hooks installed!"

pre-commit-run:
	@echo "Running pre-commit on all files..."
	$(POETRY) run pre-commit run --all-files

test:
	@echo "Running tests..."
	$(POETRY) run pytest euvd_mcp/tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	$(POETRY) run pytest euvd_mcp/tests/ -v --cov=euvd_mcp --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

lint: lint-flake8 lint-mypy lint-pylint lint-ruff

lint-flake8:
	@echo "Running Flake8..."
	$(POETRY) run flake8 . || true

lint-mypy:
	@echo "Running MyPy..."
	$(POETRY) run mypy . --ignore-missing-imports || true

lint-pylint:
	@echo "Running Pylint..."
	$(POETRY) run pylint --recursive=y . --exit-zero || true

lint-ruff:
	@echo "Running Ruff..."
	$(POETRY) run ruff check . || true

format:
	@echo "Formatting code..."
	$(POETRY) run black .
	$(POETRY) run isort .
	@echo "Code formatted!"

format-check:
	@echo "Checking code format..."
	$(POETRY) run black --check .
	$(POETRY) run isort --check-only .

security: security-bandit security-safety audit

security-bandit:
	@echo "Running Bandit security check..."
	$(POETRY) run bandit -r . -ll || true

security-safety:
	@echo "Running Safety vulnerability check..."
	$(POETRY) run safety scan --json || true

audit:
	@echo "Running pip-audit..."
	$(POETRY) run pip-audit || true

type-check:
	@echo "Running type checks..."
	$(POETRY) run mypy . --ignore-missing-imports

docker-build:
	@echo "Building Docker image..."
	$(DOCKER) build -t euvd-mcp:local .
	@echo "Docker image built: euvd-mcp:local"

docker-run:
	@echo "Running Docker container..."
	$(DOCKER) run -p 8000:8000 --env-file .env euvd-mcp:local python -m euvd_mcp.main

compose-up:
	@echo "Starting with docker-compose..."
	$(COMPOSE) up

compose-down:
	@echo "Stopping docker-compose..."
	$(COMPOSE) down

compose-logs:
	@echo "Following docker-compose logs..."
	$(COMPOSE) logs -f

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage
	rm -f coverage.xml
	@echo "Cleaned!"

clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf .venv
	@echo "All cleaned!"

pre-commit: format lint test
	@echo "Pre-commit checks passed! Ready to commit."

ci-local: clean lint test coverage security
	@echo "All CI checks passed locally!"

.DEFAULT_GOAL := help
