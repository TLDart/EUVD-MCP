# Implementation Guide

## Project Structure

```
euvdmcp/
├── controllers/
│   └── euvd_api.py      # EUVD API Manager
├── models/
│   └── vulnerability.py  # Pydantic models
├── utils/
│   └── settings.py       # Configuration
├── tests/                # 80+ tests
├── main.py              # MCP server
└── pyproject.toml       # Dependencies
```

## Getting Started

1. **Clone & Install**
   ```bash
   git clone <repository-url>
   cd euvdmcp
   poetry install
   ```

2. **Run Tests**
   ```bash
   poetry run pytest
   ```

3. **Start Server**
   ```bash
   poetry run python main.py
   ```

## Key Components

- **EUVDAPIManager** - Handles all API communication
- **Vulnerability Model** - Pydantic model for vulnerability data
- **MCP Server** - Exposes API as MCP tools

## Testing

- 80+ tests with 99% coverage
- Run with `poetry run pytest`
- See [START_HERE_TESTING.md](../testing/START_HERE_TESTING.md) for details

## CI/CD

GitHub Actions workflows for testing, linting, and deployment.
See [QUICKSTART_CI.md](../deployment/QUICKSTART_CI.md) for setup.
