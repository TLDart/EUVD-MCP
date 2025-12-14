# Testing

The test suite includes 80+ tests covering models, API manager, settings, and integration scenarios.

## Quick Start

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=controllers --cov=models --cov=utils

# Run specific test file
poetry run pytest tests/test_models.py -v
```

## Test Files

- `test_models.py` - Pydantic model validation (23 tests)
- `test_euvd_api.py` - API manager endpoints (40 tests)
- `test_settings.py` - Configuration (14 tests)
- `test_integration.py` - Integration scenarios (10+ tests)
- `conftest.py` - Fixtures and mocks

## Coverage

- **Total**: 99% code coverage
- **Models**: 100%
- **API Manager**: 96%
- **Settings**: 100%

## Common Commands

```bash
# Verbose output
poetry run pytest -v

# Show print statements
poetry run pytest -s

# Run single test
poetry run pytest tests/test_models.py::TestVulnerabilityModel -v

# Run matching pattern
poetry run pytest -k "search" -v
```
