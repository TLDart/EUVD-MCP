.PHONY: help install dev pre-commit-setup pre-commit-run \
        test test-cov \
        lint lint-ruff lint-mypy \
        format format-check \
        security security-bandit audit \
        docker-build docker-run \
        compose-up compose-down compose-logs \
        clean clean-all \
        check-env

# ── Variables ──────────────────────────────────────────────────────────────────

POETRY  := poetry
DOCKER  := docker
COMPOSE := docker-compose
IMAGE   := euvd-mcp:local

# ── Help ───────────────────────────────────────────────────────────────────────

help:
	@echo "EUVD-MCP Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install           Install production dependencies"
	@echo "  make dev               Install all dependencies (incl. dev)"
	@echo "  make pre-commit-setup  Install pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  make test              Run tests"
	@echo "  make test-cov          Run tests with HTML + terminal coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint              Run ruff lint + mypy"
	@echo "  make format            Auto-format code with ruff"
	@echo "  make format-check      Check formatting without modifying files"
	@echo "  make pre-commit-run    Run all pre-commit hooks on every file"
	@echo ""
	@echo "Security:"
	@echo "  make security          Run bandit + pip-audit"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build      Build Docker image ($(IMAGE))"
	@echo "  make docker-run        Run container — requires .env file for configuration"
	@echo "  make compose-up        Start with docker-compose (reads .env automatically)"
	@echo "  make compose-down      Stop docker-compose"
	@echo "  make compose-logs      Tail docker-compose logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean             Remove build / cache artifacts"
	@echo "  make clean-all         Remove build artifacts and virtual environment"
	@echo ""
	@echo "Note: The Docker image does NOT contain .env."
	@echo "      Configuration is injected at runtime via --env-file or -e flags."

# ── Setup ──────────────────────────────────────────────────────────────────────

install:
	@echo "Installing production dependencies..."
	$(POETRY) install --only main

dev:
	@echo "Installing all dependencies..."
	$(POETRY) install

pre-commit-setup:
	@echo "Installing pre-commit hooks..."
	$(POETRY) run pre-commit install
	@echo "Pre-commit hooks installed."

pre-commit-run:
	@echo "Running pre-commit on all files..."
	$(POETRY) run pre-commit run --all-files

# ── Testing ────────────────────────────────────────────────────────────────────

test:
	@echo "Running tests..."
	$(POETRY) run pytest

test-cov:
	@echo "Running tests with coverage..."
	$(POETRY) run pytest --cov=euvd_mcp --cov-report=html --cov-report=term
	@echo "HTML report: htmlcov/index.html"

# ── Code quality ───────────────────────────────────────────────────────────────

lint: lint-ruff lint-mypy

lint-ruff:
	@echo "Ruff lint..."
	$(POETRY) run ruff check .

lint-mypy:
	@echo "Mypy type check..."
	$(POETRY) run mypy euvd_mcp

format:
	@echo "Formatting code..."
	$(POETRY) run ruff format .
	$(POETRY) run ruff check --fix .
	@echo "Done."

format-check:
	@echo "Checking formatting..."
	$(POETRY) run ruff format --check .
	$(POETRY) run ruff check .

# ── Security ───────────────────────────────────────────────────────────────────

security: security-bandit audit

security-bandit:
	@echo "Bandit security scan (medium severity and above)..."
	$(POETRY) run bandit -r euvd_mcp -ll

audit:
	@echo "pip-audit dependency audit..."
	$(POETRY) run pip-audit

# ── Docker ─────────────────────────────────────────────────────────────────────

# Guard: abort with a clear message if .env is missing.
# The image does not embed .env — configuration must be supplied at runtime.
check-env:
	@test -f .env || { \
		echo ""; \
		echo "ERROR: .env file not found."; \
		echo "       Create one from .env.example and configure it before running the container."; \
		echo ""; \
		exit 1; \
	}

docker-build:
	@echo "Building Docker image ($(IMAGE))..."
	$(DOCKER) build -t $(IMAGE) .
	@echo "Built: $(IMAGE)"

docker-run: check-env
	@echo "Running container (config from .env)..."
	$(DOCKER) run --rm -p 8000:8000 --env-file .env $(IMAGE)

compose-up: check-env
	@echo "Starting with docker-compose..."
	$(COMPOSE) up

compose-down:
	$(COMPOSE) down

compose-logs:
	$(COMPOSE) logs -f

# ── Cleanup ────────────────────────────────────────────────────────────────────

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage coverage.xml
	@echo "Done."

clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf .venv
	@echo "Done."

.DEFAULT_GOAL := help
