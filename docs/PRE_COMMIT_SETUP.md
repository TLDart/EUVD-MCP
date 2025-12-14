# Pre-commit Hooks Setup

This project uses pre-commit hooks to enforce code quality standards and catch issues before they're committed.

## Installation

### Initial Setup

```bash
# Install all dependencies (including pre-commit)
make dev

# Install pre-commit hooks
make pre-commit-setup
```

### What Gets Installed

The `.pre-commit-config.yaml` file configures hooks for:

**Formatters:**
- **Black** - Code formatting
- **isort** - Import sorting

**Linters:**
- **Flake8** - Style guide enforcement
- **Ruff** - Fast Python linter with auto-fix
- **MyPy** - Type checking
- **Pydocstyle** - Docstring style checking

**Security:**
- **Bandit** - Security issue detection

**Other Checks:**
- **Pre-commit hooks** - Trailing whitespace, file endings, YAML validation, merge conflict detection, private keys, debug statements
- **Pytest** - Unit tests (runs on commit)
- **Pytest-cov** - Coverage verification (optional, manual stage)
- **Pylint** - Additional linting (manual stage)
- **pip-audit** - Dependency vulnerability scanning (manual stage)

## Usage

### Automatic Checks (on `git commit`)

The following hooks run automatically when you commit:

1. **Code Formatting** - Black and isort
2. **Linting** - Flake8, Ruff, MyPy, Pydocstyle
3. **Security** - Bandit checks
4. **Common Issues** - Whitespace, trailing characters, merge conflicts, private keys
5. **Tests** - Pytest unit tests

If any hook fails, the commit is blocked until you fix the issues.

### Manual Commands

Run all pre-commit checks:
```bash
make pre-commit-run
```

Run specific checks manually:
```bash
# Code formatting
make format

# Linting
make lint

# Testing
make test

# Security scanning
make security

# Coverage report (70% minimum)
make test-cov

# Type checking
make type-check
```

### Skipping Hooks (Not Recommended)

If you need to bypass pre-commit checks:
```bash
git commit --no-verify
```

⚠️ **Warning:** This should only be used in exceptional cases.

## Configuration Details

### Stages

- **commit** (default) - Runs on `git commit`
  - Code formatters
  - Linters
  - Type checking
  - Security checks
  - Pytest

- **manual** - Must be explicitly run
  - Pytest with coverage threshold (70%)
  - Pylint
  - pip-audit

### Excluded Files/Directories

The hooks automatically skip:
- `.venv/` and `venv/`
- `__pycache__/`
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- `htmlcov/`, `build/`, `dist/`
- `.git/`, `.egg-info/`

### Configuration Files

Each linter has configurations in `pyproject.toml`:

```toml
[tool.flake8]
max-line-length = 127
max-complexity = 10

[tool.mypy]
python_version = "3.12"
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["euvd_mcp/tests"]
```

## Troubleshooting

### Hook Fails on First Commit

If formatting hooks fail, they'll auto-fix most issues. Review changes and commit again:
```bash
git status
git diff
git add .
git commit
```

### Tests Fail in Pre-commit

Run tests locally to debug:
```bash
make test
```

### Type Checking Issues

Check MyPy errors:
```bash
poetry run mypy . --ignore-missing-imports
```

### Uninstall Hooks

```bash
poetry run pre-commit uninstall
```

## CI Integration

The `.pre-commit-config.yaml` includes CI-specific configuration that:
- Auto-fixes formatting issues in CI
- Skips long-running checks (tests, coverage, pip-audit) in CI
- Updates hook versions weekly

This mirrors your local setup, ensuring consistency between local development and CI pipelines.
