"""
EUVD API Manager

A Python client for interacting with the European Union Vulnerability Database (EUVD) API.
Provides methods to query vulnerabilities, advisories, and related information.
"""

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from euvd_mcp.models import (
    Advisory,
    ExploitedVulnerabilities,
    SearchResponse,
    Vulnerability,
)
from euvd_mcp.utils.settings import settings


class EUVDAPIManager:
    """
    Manager class for interacting with the EUVD API.

    All endpoints require no authentication and return JSON responses.
    """

    BASE_URL = settings.euvd_base_url

    def __init__(self, timeout: int | None = None, max_retries: int | None = None):
        """
        Initialize the EUVD API Manager.

        Args:
        ----
        timeout : int | None
            Request timeout in seconds (default: from settings or 30)
        max_retries : int | None
            Maximum number of retries for failed requests (default: from settings or 3)

        """
        self.timeout = timeout or settings.euvd_timeout
        max_retries = max_retries or settings.euvd_max_retries
        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": settings.user_agent,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://euvdservices.enisa.europa.eu/",
                "Origin": "https://euvdservices.enisa.europa.eu",
            }
        )

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[
                requests.codes.too_many_requests,
                requests.codes.internal_server_error,
                requests.codes.bad_gateway,
                requests.codes.service_unavailable,
                requests.codes.gateway_timeout,
            ],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _make_request(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """
        Make a GET request to the EUVD API.

        Args:
            endpoint: API endpoint path (e.g., '/api/lastvulnerabilities')
            params: Optional query parameters

        Returns
        -------
        Any
            JSON response as a dictionary

        Raises
        ------
        requests.RequestException
            If the request fails

        """
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Failed to fetch data from {url}: {str(e)}") from e

    def get_last_vulnerabilities(self) -> ExploitedVulnerabilities:
        """
        Get the latest vulnerabilities.

        Returns
        -------
        ExploitedVulnerabilities
            Containing up to 8 latest vulnerability records

        Example
        -------
        >>> api = EUVDAPIManager()
        >>> vulnerabilities = api.get_last_vulnerabilities()

        """
        data = self._make_request("/api/lastvulnerabilities")
        return ExploitedVulnerabilities(list=data)

    def get_exploited_vulnerabilities(self) -> ExploitedVulnerabilities:
        """
        Get the latest exploited vulnerabilities.

        Returns
        -------
        ExploitedVulnerabilities
            Containing a list of up to 8 latest exploited vulnerability records

        Example
        -------
        >>> api = EUVDAPIManager()
        >>> exploited = api.get_exploited_vulnerabilities()

        """
        data = self._make_request("/api/exploitedvulnerabilities")
        return ExploitedVulnerabilities(list=data)

    def get_critical_vulnerabilities(self) -> ExploitedVulnerabilities:
        """
        Get the latest critical vulnerabilities.

        Returns
        -------
        ExploitedVulnerabilities
            Containing up to 8 latest critical vulnerability records

        Example
        -------
        >>> api = EUVDAPIManager()
        >>> critical = api.get_critical_vulnerabilities()

        """
        data = self._make_request("/api/criticalvulnerabilities")
        return ExploitedVulnerabilities(list=data)

    def search_vulnerabilities(  # noqa: C901
        self,
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
    ) -> SearchResponse:
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
        SearchResponse
            containing search results (up to 100 records per request)

        Example
            >>> api = EUVDAPIManager()
            >>> results = api.search_vulnerabilities(
            ...     from_score=7.5,
            ...     to_score=10,
            ...     product="Windows",
            ...     exploited=True
            ... )

        """
        params = {}

        if from_score is not None:
            params["fromScore"] = from_score
        if to_score is not None:
            params["toScore"] = to_score
        if from_epss is not None:
            params["fromEpss"] = from_epss
        if to_epss is not None:
            params["toEpss"] = to_epss
        if from_date is not None:
            params["fromDate"] = from_date  # type: ignore
        if to_date is not None:
            params["toDate"] = to_date  # type: ignore
        if from_updated_date is not None:
            params["fromUpdatedDate"] = from_updated_date  # type: ignore
        if to_updated_date is not None:
            params["toUpdatedDate"] = to_updated_date  # type: ignore
        if product is not None:
            params["product"] = product  # type: ignore
        if vendor is not None:
            params["vendor"] = vendor  # type: ignore
        if assigner is not None:
            params["assigner"] = assigner  # type: ignore
        if exploited is not None:
            params["exploited"] = str(exploited).lower()  # type: ignore
        if text is not None:
            params["text"] = text  # type: ignore
        if page is not None:
            params["page"] = page
        if size is not None:
            params["size"] = size

        data = self._make_request("/api/search", params=params if params else None)
        return SearchResponse.model_validate(data)

    def get_vulnerability_by_id(self, enisa_id: str) -> Vulnerability:
        """
        Get a specific vulnerability by EUVD ID.

        Args:
            enisa_id: EUVD identifier (e.g., 'EUVD-2025-4893' or 'EUVD-2024-45012')

        Returns
        -------
        Vulnerability
            containing vulnerability details

        Example
            >>> api = EUVDAPIManager()
            >>> vuln = api.get_vulnerability_by_id("EUVD-2024-45012")

        """
        params = {"id": enisa_id}
        data = self._make_request("/api/enisaid", params=params)
        return Vulnerability.model_validate(data)

    def get_advisory_by_id(self, advisory_id: str) -> Advisory:
        """
        Get a specific advisory by ID.

        Args:
            advisory_id: Advisory identifier (e.g., 'oxas-adv-2024-0002' or 'cisco-sa-ata19x-multi-RDTEqRsy')

        Returns
        -------
        Advisory
            containing advisory details

        Example
            >>> api = EUVDAPIManager()
            >>> advisory = api.get_advisory_by_id("cisco-sa-ata19x-multi-RDTEqRsy")

        """
        params = {"id": advisory_id}
        data = self._make_request("/api/advisory", params=params)
        return Advisory.model_validate(data)

    def close(self) -> None:
        """
        Close the session and clean up resources.
        """
        self.session.close()

    def __enter__(self) -> "EUVDAPIManager":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
