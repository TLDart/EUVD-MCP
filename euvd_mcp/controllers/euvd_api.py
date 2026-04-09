"""
EUVD API Manager

A Python client for interacting with the European Union Vulnerability Database (EUVD) API.
Provides methods to query vulnerabilities, advisories, and related information.
"""

import asyncio
import logging
from time import monotonic
from typing import Any

import httpx
from cachetools import TTLCache

from euvd_mcp.models import (
    Advisory,
    ExploitedVulnerabilities,
    SearchResponse,
    Vulnerability,
)
from euvd_mcp.utils.metrics import metrics
from euvd_mcp.utils.settings import settings

logger = logging.getLogger(__name__)

_RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


class EUVDAPIManager:
    """
    Manager class for interacting with the EUVD API.

    All endpoints require no authentication and return JSON responses.
    """

    def __init__(
        self,
        timeout: int | None = None,
        max_retries: int | None = None,
        cache_ttl: int | None = None,
    ):
        """
        Initialize the EUVD API Manager.

        Args:
        ----
        timeout : int | None
            Request timeout in seconds (default: from settings or 30)
        max_retries : int | None
            Maximum number of retries for failed requests (default: from settings or 3)
        cache_ttl : int | None
            TTL in seconds for cached responses (default: from settings or 30)

        """
        self._base_url = settings.euvd_base_url
        self._timeout = timeout if timeout is not None else settings.euvd_timeout
        self._max_retries = (
            max_retries if max_retries is not None else settings.euvd_max_retries
        )
        self._cache_ttl = cache_ttl if cache_ttl is not None else settings.cache_ttl
        self._cache: TTLCache[str, Any] = TTLCache(
            maxsize=settings.cache_max_size, ttl=self._cache_ttl
        )
        self._client: httpx.AsyncClient | None = None
        logger.debug(
            "EUVDAPIManager initialised (timeout=%ds, max_retries=%d, cache_ttl=%ds)",
            self._timeout,
            self._max_retries,
            self._cache_ttl,
        )

    def _get_client(self) -> httpx.AsyncClient:
        """Return the shared async HTTP client, creating it on first use."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={
                    "User-Agent": settings.user_agent,
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Referer": "https://euvdservices.enisa.europa.eu/",
                    "Origin": "https://euvdservices.enisa.europa.eu",
                },
                timeout=self._timeout,
            )
            logger.debug("HTTP client created (timeout=%ds)", self._timeout)
        return self._client

    def _cache_get(self, key: str) -> Any | None:
        value = self._cache.get(key)
        if value is not None:
            logger.debug("Cache hit: %s", key)
            metrics.record_cache_hit()
            return value
        logger.debug("Cache miss: %s", key)
        metrics.record_cache_miss()
        return None

    def _cache_set(self, key: str, value: Any) -> None:
        self._cache[key] = value
        logger.debug("Cache set: %s (ttl=%ds)", key, self._cache_ttl)

    async def check_connectivity(self, timeout: float = 5.0) -> bool:
        """Probe the EUVD API with a short timeout. Returns True if reachable."""
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(f"{self._base_url}/api/lastvulnerabilities")
                return bool(resp.status_code < 500)
        except Exception:
            return False

    async def _make_request(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> Any:
        """
        Make a GET request to the EUVD API with automatic retries.

        Args:
            endpoint: API endpoint path (e.g., '/api/lastvulnerabilities')
            params: Optional query parameters

        Returns
        -------
        Any
            JSON response as a dictionary

        Raises
        ------
        httpx.HTTPStatusError
            If the request fails with a non-retryable HTTP error
        httpx.TransportError
            If the connection fails after all retries

        """
        url = f"{self._base_url}{endpoint}"
        client = self._get_client()
        start = monotonic()

        logger.debug("→ GET %s params=%s", endpoint, params)

        for attempt in range(self._max_retries + 1):
            try:
                response = await client.get(url, params=params)

                if (
                    response.status_code in _RETRYABLE_STATUSES
                    and attempt < self._max_retries
                ):
                    delay = 2**attempt
                    logger.warning(
                        "Retryable HTTP %d from %s — attempt %d/%d, retrying in %ds",
                        response.status_code,
                        endpoint,
                        attempt + 1,
                        self._max_retries + 1,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                response.raise_for_status()
                elapsed_ms = (monotonic() - start) * 1000
                logger.debug(
                    "← %d %s in %.0fms", response.status_code, endpoint, elapsed_ms
                )
                return response.json()

            except httpx.TransportError as exc:
                if attempt < self._max_retries:
                    delay = 2**attempt
                    logger.warning(
                        "Transport error on %s — attempt %d/%d: %s, retrying in %ds",
                        endpoint,
                        attempt + 1,
                        self._max_retries + 1,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                elapsed_ms = (monotonic() - start) * 1000
                logger.error(
                    "Request to %s failed after %d attempt(s) in %.0fms: %s",
                    endpoint,
                    self._max_retries + 1,
                    elapsed_ms,
                    exc,
                )
                raise

        # Unreachable, but satisfies the type checker
        raise RuntimeError(f"Exhausted retries for {url}")  # pragma: no cover

    async def get_last_vulnerabilities(self) -> ExploitedVulnerabilities:
        """
        Get the latest vulnerabilities.

        Returns
        -------
        ExploitedVulnerabilities
            Containing up to 8 latest vulnerability records

        Example
        -------
        >>> api = EUVDAPIManager()
        >>> vulnerabilities = await api.get_last_vulnerabilities()

        """
        cached = self._cache_get("last_vulnerabilities")
        if cached is not None:
            return cached  # type: ignore[no-any-return]
        data = await self._make_request("/api/lastvulnerabilities")
        result = ExploitedVulnerabilities(list=data)
        self._cache_set("last_vulnerabilities", result)
        return result

    async def get_exploited_vulnerabilities(self) -> ExploitedVulnerabilities:
        """
        Get the latest exploited vulnerabilities.

        Returns
        -------
        ExploitedVulnerabilities
            Containing a list of up to 8 latest exploited vulnerability records

        Example
        -------
        >>> api = EUVDAPIManager()
        >>> exploited = await api.get_exploited_vulnerabilities()

        """
        cached = self._cache_get("exploited_vulnerabilities")
        if cached is not None:
            return cached  # type: ignore[no-any-return]
        data = await self._make_request("/api/exploitedvulnerabilities")
        result = ExploitedVulnerabilities(list=data)
        self._cache_set("exploited_vulnerabilities", result)
        return result

    async def get_critical_vulnerabilities(self) -> ExploitedVulnerabilities:
        """
        Get the latest critical vulnerabilities.

        Returns
        -------
        ExploitedVulnerabilities
            Containing up to 8 latest critical vulnerability records

        Example
        -------
        >>> api = EUVDAPIManager()
        >>> critical = await api.get_critical_vulnerabilities()

        """
        cached = self._cache_get("critical_vulnerabilities")
        if cached is not None:
            return cached  # type: ignore[no-any-return]
        data = await self._make_request("/api/criticalvulnerabilities")
        result = ExploitedVulnerabilities(list=data)
        self._cache_set("critical_vulnerabilities", result)
        return result

    async def search_vulnerabilities(  # noqa: C901
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
            >>> results = await api.search_vulnerabilities(
            ...     from_score=7.5,
            ...     to_score=10,
            ...     product="Windows",
            ...     exploited=True
            ... )

        """
        params: dict[str, Any] = {}

        if from_score is not None:
            params["fromScore"] = from_score
        if to_score is not None:
            params["toScore"] = to_score
        if from_epss is not None:
            params["fromEpss"] = from_epss
        if to_epss is not None:
            params["toEpss"] = to_epss
        if from_date is not None:
            params["fromDate"] = from_date
        if to_date is not None:
            params["toDate"] = to_date
        if from_updated_date is not None:
            params["fromUpdatedDate"] = from_updated_date
        if to_updated_date is not None:
            params["toUpdatedDate"] = to_updated_date
        if product is not None:
            params["product"] = product
        if vendor is not None:
            params["vendor"] = vendor
        if assigner is not None:
            params["assigner"] = assigner
        if exploited is not None:
            params["exploited"] = str(exploited).lower()
        if text is not None:
            params["text"] = text
        if page is not None:
            params["page"] = page
        if size is not None:
            params["size"] = size

        data = await self._make_request(
            "/api/search", params=params if params else None
        )
        return SearchResponse.model_validate(data)

    async def get_vulnerability_by_id(self, enisa_id: str) -> Vulnerability:
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
            >>> vuln = await api.get_vulnerability_by_id("EUVD-2024-45012")

        """
        params = {"id": enisa_id}
        data = await self._make_request("/api/enisaid", params=params)
        return Vulnerability.model_validate(data)

    async def get_advisory_by_id(self, advisory_id: str) -> Advisory:
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
            >>> advisory = await api.get_advisory_by_id("cisco-sa-ata19x-multi-RDTEqRsy")

        """
        params = {"id": advisory_id}
        data = await self._make_request("/api/advisory", params=params)
        return Advisory.model_validate(data)

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            logger.debug("HTTP client closed")
        self._client = None

    async def __aenter__(self) -> "EUVDAPIManager":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
