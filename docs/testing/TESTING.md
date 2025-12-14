# Testing

## Test Organization

- **Unit Tests** (`test_models.py`, `test_euvd_api.py`, `test_settings.py`) - Individual components
- **Integration Tests** (`test_integration.py`) - Component interactions and workflows

## Running Tests

```bash
poetry install          # Install dependencies first
poetry run pytest       # Run all tests
poetry run pytest -v    # Verbose output
poetry run pytest --cov=. --cov-report=html  # Coverage report
```

## Test Coverage

- `test_models.py` - Model validation (23 tests, 100% coverage)
- `test_euvd_api.py` - API endpoints (40 tests, 96% coverage)
- `test_settings.py` - Configuration (14 tests, 100% coverage)
- `test_integration.py` - Workflows (10+ tests)

Overall: **99% code coverage**

## Specific Commands

```bash
# Run single file
poetry run pytest tests/test_models.py

# Run matching pattern
poetry run pytest -k "search"

# Run single test
poetry run pytest tests/test_euvd_api.py::TestSearchVulnerabilities::test_search_basic

# Integration tests only
poetry run pytest -m integration

# With detailed output
poetry run pytest -vv -s
```

## Fixtures

Test fixtures are defined in `conftest.py`:
- `sample_vulnerability` - Single vulnerability object
- `sample_vulnerabilities_list` - Multiple vulnerabilities
- `sample_search_response` - Paginated results
- `sample_advisory` - Advisory object
- Mocked HTTP responses for all endpoints
