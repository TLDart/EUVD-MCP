# CI/CD Setup

## Overview

This project uses GitHub Actions for CI/CD. On every push/PR:
- Tests run (80+ tests)
- Code is linted (Flake8, MyPy, Black, isort)
- Security scans (Bandit, Safety)
- Docker image is built

## Local Development

```bash
# Setup
poetry install

# Before committing
poetry run black .
poetry run isort .
poetry run flake8 .
poetry run mypy .
poetry run pytest tests/ -v

# Push & create PR on GitHub
git checkout -b feature/your-feature
git add .
git commit -m "Your message"
git push origin feature/your-feature
```

## CI Workflows

Available in `.github/workflows/`:

- **ci.yml** - Main testing and linting
- **deploy.yml** - Deployment and releases
- **code-quality.yml** - Code quality checks

## Docker

```bash
# Build the image
docker build -t euvd-mcp:test .

# Run the container
docker run -p 8000:8000 --env-file .env euvd-mcp:test

# Or use docker-compose
docker-compose up
```

## Troubleshooting

**Tests fail?**
- Run `poetry run pytest tests/ -v` locally
- Check error message and fix

**Linting issues?**
- Run `poetry run black .` to auto-format
- Run `poetry run flake8 .` to see remaining issues

**Docker build fails?**
- Run `docker build -t test:latest .` locally
- Check pyproject.toml dependencies

## Common Commands

```bash
# Check before pushing
poetry run black --check .
poetry run flake8 .
poetry run mypy .
poetry run pytest tests/ -v

# Auto-fix code
poetry run black .
poetry run isort .

# View coverage report
poetry run pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

See [README_CI_CD.md](README_CI_CD.md) for more details.
