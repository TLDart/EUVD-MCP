"""
EUVD MCP Server

Model Context Protocol server for the European Union Vulnerability Database (EUVD) API.
Exposes EUVD API functionality as MCP tools.
"""

from typing import Any

from fastmcp import FastMCP

from euvd_mcp.controllers.euvd_api import EUVDAPIManager
from euvd_mcp.utils.settings import settings

# Create MCP server instance
mcp = FastMCP("EUVD API")

# Initialize API manager (will be reused across tool calls)
api_manager = EUVDAPIManager()


@mcp.tool()  # type: ignore[misc]
def get_last_vulnerabilities() -> dict[str, Any]:
    """
    Get the latest vulnerabilities from the EUVD database.

    Returns up to 8 latest vulnerability records.

    Returns
    -------
    dict
        Dictionary containing the latest vulnerabilities

    """
    response = api_manager.get_last_vulnerabilities()
    return response.model_dump(mode="json")


@mcp.tool()  # type: ignore[misc]
def get_exploited_vulnerabilities() -> dict[str, Any]:
    """
    Get the latest exploited vulnerabilities from the EUVD database.

    Returns up to 8 latest exploited vulnerability records.

    Returns
    -------
    dict
        Dictionary containing the latest exploited vulnerabilities

    """
    response = api_manager.get_exploited_vulnerabilities()
    return response.model_dump(mode="json")


@mcp.tool()  # type: ignore[misc]
def get_critical_vulnerabilities() -> dict[str, Any]:
    """
    Get the latest critical vulnerabilities from the EUVD database.

    Returns up to 8 latest critical vulnerability records.

    Returns
    -------
    dict
        Dictionary containing the latest critical vulnerabilities

    """
    response = api_manager.get_critical_vulnerabilities()
    return response.model_dump(mode="json")


@mcp.tool()  # type: ignore[misc]
def search_vulnerabilities(
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
    """
    Search vulnerabilities with flexible filters.

    Args:
        from_score: Minimum CVSS score (0-10)
        to_score: Maximum CVSS score (0-10)
        from_epss: Minimum EPSS score (0-100)
        to_epss: Maximum EPSS score (0-100)
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        from_updated_date: Start updated date in YYYY-MM-DD format
        to_updated_date: End updated date in YYYY-MM-DD format
        product: Product name filter (e.g., 'Windows')
        vendor: Vendor name filter (e.g., 'Microsoft')
        assigner: Assigner filter (e.g., 'mitre')
        exploited: Filter by exploited status (True/False)
        text: Keyword search
        page: Page number (starts at 0)
        size: Page size (default 10, max 100)

    Returns
    -------
    dict
        Dictionary containing search results (up to 100 records per request)

    """
    response = api_manager.search_vulnerabilities(
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
    return response.model_dump(mode="json")


@mcp.tool  # type: ignore[misc]
def get_vulnerability_by_id(enisa_id: str) -> dict[str, Any]:
    """
    Get a specific vulnerability by EUVD ID.

    Args:
        enisa_id: EUVD identifier (e.g., 'EUVD-2025-4893' or 'EUVD-2024-45012')

    Returns
    -------
    dict
        Dictionary containing vulnerability details

    """
    vulnerability = api_manager.get_vulnerability_by_id(enisa_id)
    return vulnerability.model_dump(mode="json")


@mcp.tool()  # type: ignore[misc]
def get_advisory_by_id(advisory_id: str) -> dict[str, Any]:
    """
    Get a specific advisory by ID.

    Args:
        advisory_id: Advisory identifier (e.g., 'oxas-adv-2024-0002' or 'cisco-sa-ata19x-multi-RDTEqRsy')

    Returns
    -------
    dict
        Dictionary containing advisory details

    """
    advisory = api_manager.get_advisory_by_id(advisory_id)
    return advisory.model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(transport="http", host=settings.host, port=settings.port)
