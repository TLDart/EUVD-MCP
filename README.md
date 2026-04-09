# EUVD-MCP

MCP server for the [European Union Vulnerability Database](https://euvdservices.enisa.europa.eu/) (EUVD) maintained by ENISA.

## Features

- Search vulnerabilities with flexible filters (CVSS, EPSS, dates, product, vendor, exploited status, etc.)
- Get latest, critical, and exploited vulnerabilities
- Lookup specific vulnerabilities and advisories by ID
- Automatic retries with exponential backoff
- Bounded TTL cache (`cachetools.TTLCache`) for list endpoints
- Structured logging (always to stderr — safe for stdio transport)
- `/health` liveness endpoint and `/metrics` observability endpoint (HTTP mode)
- Startup connectivity check to the EUVD API
- Two transport modes: **HTTP** (standalone/Docker) and **stdio** (subprocess/Claude Desktop)

## Requirements

- Python 3.14+
- [Poetry](https://python-poetry.org/)

## Installation

```bash
git clone <repository-url>
cd euvdmcp
poetry install
```

Copy the example environment file and adjust as needed:

```bash
cp .env.template .env
```

## Configuration

All settings are read from environment variables (or a `.env` file at the project root).

| Variable | Default | Description |
|---|---|---|
| `TRANSPORT` | `http` | Transport mode: `http` or `stdio` |
| `HOST` | `127.0.0.1` | Server bind address (HTTP mode only) |
| `PORT` | `8000` | Server port (HTTP mode only) |
| `EUVD_BASE_URL` | `https://euvdservices.enisa.europa.eu` | EUVD API base URL |
| `EUVD_TIMEOUT` | `30` | HTTP request timeout (seconds) |
| `EUVD_MAX_RETRIES` | `3` | Max retries on transient failures |
| `CACHE_TTL` | `30` | TTL for cached list responses (seconds) |
| `CACHE_MAX_SIZE` | `128` | Maximum entries in the response cache |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `USER_AGENT` | `euvd-mcp-tool` | User-Agent header sent to the EUVD API |

## Running

### uvicorn (recommended)

```bash
uvicorn euvd_mcp.main:app --host 127.0.0.1 --port 8000
```

With live reload during development:

```bash
uvicorn euvd_mcp.main:app --host 127.0.0.1 --port 8000 --reload
```

### Poetry

```bash
poetry run python -m euvd_mcp.main
```

Server runs on `http://127.0.0.1:8000/mcp` by default.

### Docker

Build the image:

```bash
make docker-build
```

Run with a `.env` file (configuration is **not** baked into the image):

```bash
make docker-run        # uses .env automatically
```

Or docker-compose:

```bash
make compose-up        # start
make compose-logs      # tail logs
make compose-down      # stop
```

### stdio (Claude Desktop / subprocess)

```bash
TRANSPORT=stdio poetry run python -m euvd_mcp.main
```

> **Note:** In stdio mode the `/health` and `/metrics` endpoints are not available. Logs go to stderr so they do not interfere with the MCP protocol on stdout.

## Integrating with LLM Clients

### Claude Desktop — HTTP (server running separately)

Add to your Claude Desktop configuration file:

**macOS/Linux:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "euvd": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

### Claude Desktop — stdio (subprocess)

```json
{
  "mcpServers": {
    "euvd": {
      "command": "poetry",
      "args": ["run", "python", "-m", "euvd_mcp.main"],
      "env": { "TRANSPORT": "stdio" }
    }
  }
}
```

### Claude Desktop — Docker

```json
{
  "mcpServers": {
    "euvd": {
      "command": "docker",
      "args": [
        "run", "--rm", "-p", "8000:8000",
        "--env-file", "/absolute/path/to/.env",
        "euvd-mcp:local"
      ]
    }
  }
}
```

### Example queries

- "What are the latest critical vulnerabilities?"
- "Search for exploited vulnerabilities with CVSS score above 8.0"
- "Get details for vulnerability EUVD-2024-45012"
- "Find vulnerabilities from Microsoft published in the last 30 days"

## Available Tools

| Tool | Description |
|---|---|
| `get_last_vulnerabilities` | Latest vulnerabilities (up to 8) |
| `get_exploited_vulnerabilities` | Latest exploited vulnerabilities |
| `get_critical_vulnerabilities` | Latest critical vulnerabilities (CVSS ≥ 9.0) |
| `search_vulnerabilities` | Search with CVSS, EPSS, date, vendor, product, and exploited filters |
| `get_vulnerability_by_id` | Fetch a single vulnerability by EUVD ID (e.g. `EUVD-2024-45012`) |
| `get_advisory_by_id` | Fetch an advisory by its vendor-assigned ID |

## Observability

Two endpoints are available in HTTP mode:

| Endpoint | Description |
|---|---|
| `GET /health` | Liveness probe — returns `{"status": "ok", "version": "...", "uptime_seconds": N}` |
| `GET /metrics` | Request counts, per-tool latencies, cache hit/miss ratio, error breakdown |

## Project Structure

```
euvdmcp/
├── euvd_mcp/
│   ├── main.py                    # MCP server, tool definitions, health/metrics routes
│   ├── controllers/
│   │   └── euvd_api.py            # Async API client with retry and TTL cache
│   ├── models/
│   │   ├── input_models.py        # Pydantic input validation models
│   │   └── vulnerability.py       # Response data models
│   ├── utils/
│   │   ├── settings.py            # Configuration (pydantic-settings)
│   │   ├── logging_config.py      # Structured logging setup
│   │   └── metrics.py             # In-process metrics collector
│   └── tests/                     # pytest test suite
├── Dockerfile                     # Multi-stage build, non-root user, HEALTHCHECK
├── docker-compose.yml
├── Makefile
└── pyproject.toml
```

## Development

```bash
poetry install                 # install all dependencies (incl. dev)
make pre-commit-setup          # install git hooks
make test                      # run tests
make test-cov                  # run tests with coverage report
make lint                      # ruff + mypy
make format                    # auto-format with ruff
make security                  # bandit + pip-audit
```

## CI

Three GitHub Actions workflows run on every PR to `main`:

- **CI** — tests, security scan (bandit + pip-audit), lock-file check, Docker build
- **Code Quality** — ruff lint/format, mypy type check, markdown validation
- **Security Scan** — Trivy container scan, results uploaded to GitHub Security tab

## License

See [LICENSE](LICENSE)

## Author

Duarte Dias

## Acknowledgments

- [ENISA](https://www.enisa.europa.eu/) — European Union Agency for Cybersecurity
- [FastMCP](https://github.com/jlowin/fastmcp) — MCP framework
