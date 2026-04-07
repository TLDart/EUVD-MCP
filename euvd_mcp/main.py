"""
EUVD MCP Server

Model Context Protocol server for the European Union Vulnerability Database (EUVD) API.
Exposes EUVD API functionality as MCP tools.
"""

import functools
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from time import monotonic
from typing import Any, Callable

import httpx
from fastmcp import FastMCP
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from euvd_mcp.controllers.euvd_api import EUVDAPIManager
from euvd_mcp.models import (
    GetAdvisoryByIdInput,
    GetVulnerabilityByIdInput,
    SearchVulnerabilitiesInput,
)
from euvd_mcp.utils.logging_config import configure_logging
from euvd_mcp.utils.metrics import metrics
from euvd_mcp.utils.settings import settings

try:
    _APP_VERSION = _pkg_version("euvd-mcp")
except PackageNotFoundError:
    _APP_VERSION = "unknown"

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


def _format_validation_error(exc: ValidationError) -> str:
    """Return a concise, LLM-readable summary of a Pydantic ValidationError."""
    parts = []
    for error in exc.errors():
        loc = ".".join(str(x) for x in error["loc"]) if error["loc"] else "input"
        parts.append(f"{loc}: {error['msg']}")
    return "; ".join(parts)


def _handle_tool_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Catch all expected exceptions from a tool function and return a structured error dict.

    Error codes returned in the ``error`` field:
    - ``validation_error``  — invalid input; the LLM should fix its parameters.
    - ``http_error``        — the EUVD API returned an HTTP error; includes ``status_code``.
    - ``connection_error``  — the EUVD API could not be reached; try again later.
    - ``unexpected_error``  — an unhandled exception; details are in the server logs.
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        start = monotonic()
        try:
            return await func(*args, **kwargs)  # type: ignore[no-any-return]

        except ValidationError as exc:
            detail = _format_validation_error(exc)
            logger.warning("tool=%s validation_error: %s", func.__name__, detail)
            metrics.record_error(func.__name__, "validation_error")
            return {
                "error": "validation_error",
                "detail": detail,
            }

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            log = logger.error if status >= 500 else logger.warning
            log(
                "tool=%s http_error: status=%d url=%s",
                func.__name__,
                status,
                exc.request.url,
            )
            metrics.record_error(func.__name__, "http_error")
            return {
                "error": "http_error",
                "status_code": status,
                "detail": _http_error_detail(status),
            }

        except httpx.TransportError as exc:
            logger.error("tool=%s connection_error: %s", func.__name__, exc)
            metrics.record_error(func.__name__, "connection_error")
            return {
                "error": "connection_error",
                "detail": f"Unable to reach the EUVD API: {exc}",
            }

        except Exception as exc:  # noqa: BLE001
            logger.exception("tool=%s unexpected_error: %s", func.__name__, exc)
            metrics.record_error(func.__name__, "unexpected_error")
            return {
                "error": "unexpected_error",
                "detail": "An unexpected error occurred. Check the server logs for details.",
            }

        finally:
            metrics.record_request(func.__name__, (monotonic() - start) * 1000)

    return wrapper


def _http_error_detail(status: int) -> str:
    messages = {
        400: "The request was malformed. This is likely a bug — please report it.",
        401: "Authentication required by the EUVD API (unexpected; the API is public).",
        403: "Access denied by the EUVD API.",
        404: "The requested resource was not found. Verify the ID is correct.",
        429: "The EUVD API rate limit was reached. Wait a moment before retrying.",
        500: "The EUVD API returned an internal server error. Try again later.",
        502: "The EUVD API is temporarily unavailable (bad gateway). Try again later.",
        503: "The EUVD API is temporarily unavailable (service unavailable). Try again later.",
        504: "The EUVD API timed out. Try again later.",
    }
    return messages.get(status, f"The EUVD API returned HTTP {status}.")


# Initialize API manager (shared across all tool calls)
api_manager = EUVDAPIManager()


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncGenerator[None, None]:
    """Manage API client lifecycle and run a startup connectivity check."""
    logger.info(
        "EUVD MCP server starting up (version=%s, log_level=%s)",
        _APP_VERSION,
        settings.log_level,
    )
    async with api_manager:
        reachable = await api_manager.check_connectivity()
        if reachable:
            logger.info(
                "EUVD API connectivity check passed (%s)", settings.euvd_base_url
            )
        else:
            logger.warning(
                "EUVD API connectivity check failed (%s) — tools will return connection errors until restored",
                settings.euvd_base_url,
            )
        yield
    logger.info("EUVD MCP server shut down")


# Create MCP server instance
mcp = FastMCP(
    "EUVD API",
    lifespan=lifespan,
    instructions=(
        "This server provides access to the European Union Vulnerability Database (EUVD), "
        "maintained by ENISA (European Union Agency for Cybersecurity). "
        "It contains security vulnerabilities identified by ENISA IDs (e.g. EUVD-2024-45012) "
        "which may map to one or more CVE identifiers. "
        "Each vulnerability record includes a CVSS score (severity 0-10, where >=9.0 is Critical, "
        ">=7.0 High, >=4.0 Medium) and an EPSS score (probability 0-100% that the vulnerability "
        "will be exploited in the next 30 days). "
        "Use search_vulnerabilities for targeted queries. Use the get_last/exploited/critical "
        "tools for situational awareness of the current threat landscape. "
        "If a tool returns a dict with an 'error' key, inspect the 'detail' field to understand "
        "the failure and decide whether to retry, correct your parameters, or inform the user."
    ),
)


if settings.transport == "http":
    # Custom routes only make sense over HTTP — stdio has no HTTP server.
    @mcp.custom_route("/health", methods=["GET"])  # type: ignore[misc]
    async def health_check(request: Request) -> JSONResponse:
        """Liveness probe — returns 200 while the server is running."""
        return JSONResponse(
            {
                "status": "ok",
                "version": _APP_VERSION,
                "uptime_seconds": round(metrics.uptime_seconds, 2),
            }
        )

    @mcp.custom_route("/metrics", methods=["GET"])  # type: ignore[misc]
    async def metrics_endpoint(request: Request) -> JSONResponse:
        """Operational metrics: request counts, latencies, cache stats, error breakdown."""
        return JSONResponse(metrics.to_dict())


@mcp.tool()  # type: ignore[misc]
@_handle_tool_errors
async def get_last_vulnerabilities() -> dict[str, Any]:
    """
    Return the 8 most recently published vulnerabilities in the EUVD database.

    Use this tool when the user asks about the newest or most recently disclosed
    vulnerabilities, regardless of their severity or exploitation status.
    Results are ordered by publication date (newest first).

    Each record includes: ENISA ID, CVE aliases, description, CVSS base score and
    vector, EPSS score, publication and update dates, affected products and vendors,
    and links to source advisories.

    Prefer get_exploited_vulnerabilities when the user is concerned about active
    threats, or get_critical_vulnerabilities when they want the most severe ones.
    """
    logger.info("tool=get_last_vulnerabilities")
    response = await api_manager.get_last_vulnerabilities()
    return response.model_dump(mode="json")


@mcp.tool()  # type: ignore[misc]
@_handle_tool_errors
async def get_exploited_vulnerabilities() -> dict[str, Any]:
    """Return the 8 most recently recorded vulnerabilities actively exploited in the wild.

    Use this tool when the user asks about active threats, in-the-wild attacks,
    known exploited vulnerabilities (KEV), or which vulnerabilities attackers are
    currently leveraging. These are the highest operational priority for patching.

    Each record includes: ENISA ID, CVE aliases, description, CVSS base score and
    vector, EPSS score, publication and update dates, affected products and vendors,
    and links to source advisories.

    Prefer get_critical_vulnerabilities when severity (CVSS score) matters more
    than confirmed exploitation, or search_vulnerabilities to filter by specific
    products, vendors, or date ranges.
    """
    logger.info("tool=get_exploited_vulnerabilities")
    response = await api_manager.get_exploited_vulnerabilities()
    return response.model_dump(mode="json")


@mcp.tool()  # type: ignore[misc]
@_handle_tool_errors
async def get_critical_vulnerabilities() -> dict[str, Any]:
    """Return the 8 most recently published vulnerabilities with a critical CVSS score (9.0-10.0).

    Use this tool when the user wants to know about the most severe recent
    vulnerabilities, or when assessing the worst-case exposure across all software.
    Critical vulnerabilities often allow unauthenticated remote code execution or
    complete system compromise.

    Each record includes: ENISA ID, CVE aliases, description, CVSS base score and
    vector, EPSS score, publication and update dates, affected products and vendors,
    and links to source advisories.

    Prefer get_exploited_vulnerabilities when confirmed in-the-wild exploitation is
    the priority, or search_vulnerabilities to narrow results by product or vendor.
    """
    logger.info("tool=get_critical_vulnerabilities")
    response = await api_manager.get_critical_vulnerabilities()
    return response.model_dump(mode="json")


@mcp.tool()  # type: ignore[misc]
@_handle_tool_errors
async def search_vulnerabilities(
    from_score: float | None = None,
    to_score: float | None = None,
    from_epss: float | None = None,
    to_epss: float | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    from_updated_date: str | None = None,
    to_updated_date: str | None = None,
    product: str | None = None,
    vendor: str | None = None,
    assigner: str | None = None,
    exploited: bool | None = None,
    text: str | None = None,
    page: int | None = None,
    size: int | None = None,
) -> dict[str, Any]:
    """Search the EUVD for vulnerabilities matching any combination of filters.

    Returns a paginated list of matching records (default 10, up to 100 per page).

    Use this tool for any targeted vulnerability query, such as:
    - "Find critical vulnerabilities in Apache published this year"
    - "Show exploited vulnerabilities affecting Windows from the last 30 days"
    - "What vulnerabilities does Microsoft have with CVSS >= 9.0?"
    - "Find vulnerabilities with high exploitation probability (EPSS > 80%)"

    All filters are optional and combinable. Omit any filter to leave it unrestricted.

    Args:
        from_score: Minimum CVSS base score (0.0–10.0). Use 9.0 for Critical,
            7.0 for High and above, 4.0 for Medium and above.
        to_score: Maximum CVSS base score (0.0–10.0).
        from_epss: Minimum EPSS score (0.0–100.0). EPSS is the probability (%)
            that the vulnerability will be exploited in the next 30 days.
            Use 50 or higher to focus on likely-to-be-exploited vulnerabilities.
        to_epss: Maximum EPSS score (0.0–100.0).
        from_date: Earliest publication date (YYYY-MM-DD). Use to scope results
            to a specific time window, e.g. the current year or last 30 days.
        to_date: Latest publication date (YYYY-MM-DD).
        from_updated_date: Earliest last-updated date (YYYY-MM-DD). Useful for
            finding recently re-scored or re-assessed vulnerabilities.
        to_updated_date: Latest last-updated date (YYYY-MM-DD).
        product: Filter by affected product name (case-insensitive partial match,
            e.g. 'Windows', 'OpenSSL', 'Apache HTTP Server').
        vendor: Filter by vendor/manufacturer name (e.g. 'Microsoft', 'Apache',
            'Cisco', 'Linux').
        assigner: Filter by the CVE numbering authority that assigned the CVE
            (e.g. 'mitre', 'microsoft', 'redhat').
        exploited: Set True to return only vulnerabilities with confirmed
            in-the-wild exploitation. Set False to exclude exploited ones.
        text: Free-text keyword search across vulnerability descriptions and
            identifiers (e.g. 'remote code execution', 'privilege escalation').
        page: Zero-based page number for pagination (default 0).
        size: Number of results per page, between 1 and 100 (default 10).
    """
    params = SearchVulnerabilitiesInput(
        from_score=from_score,
        to_score=to_score,
        from_epss=from_epss,
        to_epss=to_epss,
        from_date=from_date,
        to_date=to_date,
        from_updated_date=from_updated_date,
        to_updated_date=to_updated_date,
        product=product,
        vendor=vendor,
        assigner=assigner,
        exploited=exploited,
        text=text,
        page=page,
        size=size,
    )
    logger.info(
        "tool=search_vulnerabilities params=%s", params.model_dump(exclude_none=True)
    )
    response = await api_manager.search_vulnerabilities(
        **params.model_dump(exclude_none=True)
    )
    return response.model_dump(mode="json")


@mcp.tool()  # type: ignore[misc]
@_handle_tool_errors
async def get_vulnerability_by_id(enisa_id: str) -> dict[str, Any]:
    """
    Retrieve the full details of a single vulnerability by its ENISA/EUVD identifier.

    Use this tool when you already have a specific EUVD ID (obtained from a prior
    search or provided by the user) and need its complete record, including all
    affected products and vendors, linked CVEs, CVSS vector, EPSS score, references,
    and associated advisories.

    EUVD IDs follow the format EUVD-YYYY-N (e.g. 'EUVD-2024-45012', 'EUVD-2025-4893').
    They are distinct from CVE IDs — if the user provides a CVE ID instead, use
    search_vulnerabilities with the text parameter to find the corresponding record.

    Args:
        enisa_id: EUVD identifier in EUVD-YYYY-N format (e.g. 'EUVD-2024-45012').
    """
    validated = GetVulnerabilityByIdInput(enisa_id=enisa_id)
    logger.info("tool=get_vulnerability_by_id enisa_id=%s", validated.enisa_id)
    vulnerability = await api_manager.get_vulnerability_by_id(validated.enisa_id)
    return vulnerability.model_dump(mode="json")


@mcp.tool()  # type: ignore[misc]
@_handle_tool_errors
async def get_advisory_by_id(advisory_id: str) -> dict[str, Any]:
    """
    Retrieve a specific vendor or source advisory by its advisory ID.

    Advisories are official security bulletins published by vendors (e.g. Cisco,
    Microsoft, Red Hat) or coordination bodies. They often cover multiple CVEs and
    provide remediation guidance, workarounds, and affected version details.

    Use this tool when the user references a specific advisory ID, or when a
    vulnerability record from search/lookup contains advisory references you want
    to expand. Advisory IDs appear in EUVD vulnerability records under
    enisaIdAdvisory or vulnerabilityAdvisory fields.

    The response includes: advisory description and summary, publication and update
    dates, CVSS score, source organisation, affected products, linked EUVD entries,
    and associated CVEs.

    Args:
        advisory_id: Advisory identifier as issued by the source organisation
            (e.g. 'cisco-sa-ata19x-multi-RDTEqRsy', 'oxas-adv-2024-0002').
    """
    validated = GetAdvisoryByIdInput(advisory_id=advisory_id)
    logger.info("tool=get_advisory_by_id advisory_id=%s", validated.advisory_id)
    advisory = await api_manager.get_advisory_by_id(validated.advisory_id)
    return advisory.model_dump(mode="json")


if __name__ == "__main__":
    if settings.transport == "stdio":
        logger.info(
            "Starting in stdio transport mode — /health and /metrics are unavailable"
        )
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="http", host=settings.host, port=settings.port)
