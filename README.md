# EUVD-MCP

MCP server for the European Union Vulnerability Database API.

## Features

- Search vulnerabilities with flexible filters (CVSS, EPSS, dates, product, vendor, etc.)
- Get latest, critical, and exploited vulnerabilities
- Lookup specific vulnerabilities and advisories
- Automatic retries for resilient API calls

## Installation

Prerequisites: Python 3.12+, Poetry

```bash
git clone <repository-url>
cd euvdmcp
poetry install
```


## Usage

Start the server:
```bash
poetry run python main.py
```

Server runs on `http://127.0.0.1:8000/mcp` by default.

Use the API directly:
```python
from controllers.euvd_api import EUVDAPIManager

with EUVDAPIManager() as api:
    vulnerabilities = api.get_last_vulnerabilities()
    results = api.search_vulnerabilities(from_score=7.5, exploited=True)
    vuln = api.get_vulnerability_by_id("EUVD-2024-45012")
```

## Available Tools

- **get_last_vulnerabilities** - Latest vulnerabilities (up to 8)
- **get_exploited_vulnerabilities** - Latest exploited vulnerabilities
- **get_critical_vulnerabilities** - Latest critical vulnerabilities
- **search_vulnerabilities** - Search with filters (CVSS, EPSS, dates, product, vendor, exploited status, etc.)
- **get_vulnerability_by_id** - Get specific vulnerability by EUVD ID
- **get_advisory_by_id** - Get advisory by ID

## API Endpoints

- `GET /api/lastvulnerabilities` - Latest vulnerabilities
- `GET /api/exploitedvulnerabilities` - Exploited vulnerabilities
- `GET /api/criticalvulnerabilities` - Critical vulnerabilities
- `GET /api/search` - Search vulnerabilities
- `GET /api/enisaid` - Get by EUVD ID
- `GET /api/advisory` - Get advisory

Details: https://euvdservices.enisa.europa.eu/

## Project Structure

```
euvdmcp/
├── controllers/euvd_api.py     # API Manager
├── models/vulnerability.py      # Data models
├── utils/settings.py            # Configuration
├── tests/                       # 80+ tests
└── main.py                      # MCP server
```

## Testing

80+ tests with 99% coverage. Run with:
```bash
poetry run pytest
poetry run pytest --cov=controllers --cov=models --cov=utils
```

See [docs/testing/START_HERE_TESTING.md](docs/testing/START_HERE_TESTING.md)

## Documentation

- [docs/INDEX.md](docs/INDEX.md) - Documentation index
- [docs/testing/START_HERE_TESTING.md](docs/testing/START_HERE_TESTING.md) - Testing guide
- [docs/deployment/QUICKSTART_CI.md](docs/deployment/QUICKSTART_CI.md) - CI/CD setup
- [docs/guides/README_IMPLEMENTATION.md](docs/guides/README_IMPLEMENTATION.md) - Implementation guide

## License

See [LICENSE](LICENSE)

## Author

Duarte Dias <me@duartedias.me>

## Acknowledgments

- [ENISA](https://www.enisa.europa.eu/) - European Union Agency for Cybersecurity
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP library
