# CI/CD Pipeline

## Overview

GitHub Actions automates testing, linting, building, and deployment.

## What Runs Automatically

### On Every Push/PR
- Unit tests (80+ tests with 99% coverage)
- Code linting (Flake8, MyPy)
- Code formatting check (Black, isort)
- Security scanning (Bandit, Safety)
- Docker image build

### On Main Branch Push
- Docker image pushed to GHCR
- Additional security scans

### On Version Tag (v*.*.*)
- Automatic GitHub Release created

## Workflows

Available in `.github/workflows/`:

| File | Purpose |
|------|---------|
| `ci.yml` | Main testing and linting pipeline |
| `deploy.yml` | Build, push Docker, and create releases |
| `code-quality.yml` | Code quality and security checks |

## Configuration Files

| File | Purpose |
|------|---------|
| `.flake8` | Python linting rules |
| `mypy.ini` | Type checking configuration |
| `pytest.ini` | Testing configuration |
| `Makefile` | Development shortcuts |

## Key Features

- ✅ All tests must pass before merge
- ✅ Code coverage tracked and enforced
- ✅ Security vulnerabilities scanned
- ✅ Docker images automatically built and pushed
- ✅ Automated dependency updates with Dependabot

## Getting Started

See [QUICKSTART_CI.md](QUICKSTART_CI.md) for development workflow.
