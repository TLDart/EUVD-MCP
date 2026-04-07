"""
Unit tests for the EUVD API Manager.
"""

import httpx
import pytest

from euvd_mcp.controllers.euvd_api import EUVDAPIManager
from euvd_mcp.models import Advisory, SearchResponse, Vulnerability


class TestEUVDAPIManagerInit:
    """Test EUVDAPIManager initialization."""

    def test_api_manager_default_init(self):
        """Test initializing API manager with defaults."""
        manager = EUVDAPIManager()
        assert manager._timeout > 0
        assert manager._client is None  # lazy initialization

    def test_api_manager_custom_timeout(self):
        """Test initializing API manager with custom timeout."""
        manager = EUVDAPIManager(timeout=60)
        assert manager._timeout == 60

    def test_api_manager_custom_retries(self):
        """Test initializing API manager with custom max retries."""
        manager = EUVDAPIManager(max_retries=5)
        assert manager._max_retries == 5

    def test_api_manager_custom_cache_ttl(self):
        """Test initializing API manager with custom cache TTL."""
        manager = EUVDAPIManager(cache_ttl=60)
        assert manager._cache_ttl == 60

    def test_get_client_creates_async_client(self):
        """Test that _get_client creates an httpx.AsyncClient."""
        manager = EUVDAPIManager()
        client = manager._get_client()
        assert isinstance(client, httpx.AsyncClient)

    def test_get_client_returns_same_instance(self):
        """Test that _get_client returns the same client on repeated calls."""
        manager = EUVDAPIManager()
        assert manager._get_client() is manager._get_client()

    def test_client_headers_are_set(self):
        """Test that the HTTP client has the expected headers."""
        manager = EUVDAPIManager()
        client = manager._get_client()
        assert "User-Agent" in client.headers
        assert "Accept" in client.headers


class TestEUVDAPIManagerRequests:
    """Test API request methods."""

    async def test_make_request_success(self, api_manager, httpx_mock):
        """Test successful API request."""
        httpx_mock.add_response(json={"id": "test"})
        result = await api_manager._make_request("/api/test")
        assert result == {"id": "test"}

    async def test_make_request_with_params(self, api_manager, httpx_mock):
        """Test API request with query parameters."""
        httpx_mock.add_response(json={"results": []})
        params = {"fromScore": 7.5, "toScore": 10}
        result = await api_manager._make_request("/api/search", params=params)
        assert result == {"results": []}
        sent = httpx_mock.get_requests()[0]
        assert "fromScore=7.5" in str(sent.url)

    async def test_make_request_transport_error(self, api_manager, httpx_mock):
        """Test that transport errors are raised after retries."""
        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))
        with pytest.raises(httpx.TransportError):
            await api_manager._make_request("/api/test")

    async def test_make_request_http_status_error(self, api_manager, httpx_mock):
        """Test that non-retryable HTTP errors are raised immediately."""
        httpx_mock.add_response(status_code=404)
        with pytest.raises(httpx.HTTPStatusError):
            await api_manager._make_request("/api/test")


class TestGetLastVulnerabilities:
    """Test get_last_vulnerabilities method."""

    async def test_get_last_vulnerabilities_success(
        self, api_manager, httpx_mock, sample_vulnerabilities_list
    ):
        """Test successful retrieval of last vulnerabilities."""
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        result = await api_manager.get_last_vulnerabilities()
        assert result.list is not None
        assert len(result.list) == 2

    async def test_get_last_vulnerabilities_endpoint(
        self, api_manager, httpx_mock, sample_vulnerabilities_list
    ):
        """Test that correct endpoint is called."""
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        await api_manager.get_last_vulnerabilities()
        assert "/api/lastvulnerabilities" in str(httpx_mock.get_requests()[0].url)

    async def test_get_last_vulnerabilities_cached(
        self, api_manager, httpx_mock, sample_vulnerabilities_list
    ):
        """Test that second call returns cached result without a new request."""
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        result1 = await api_manager.get_last_vulnerabilities()
        result2 = await api_manager.get_last_vulnerabilities()
        assert result1 is result2
        assert len(httpx_mock.get_requests()) == 1

    async def test_get_last_vulnerabilities_cache_miss_after_expiry(
        self, httpx_mock, sample_vulnerabilities_list
    ):
        """Test that an expired cache entry triggers a new request."""
        manager = EUVDAPIManager(timeout=10, max_retries=0, cache_ttl=0)
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        await manager.get_last_vulnerabilities()
        await manager.get_last_vulnerabilities()
        assert len(httpx_mock.get_requests()) == 2


class TestGetExploitedVulnerabilities:
    """Test get_exploited_vulnerabilities method."""

    async def test_get_exploited_vulnerabilities_success(
        self, api_manager, httpx_mock, sample_vulnerabilities_list
    ):
        """Test successful retrieval of exploited vulnerabilities."""
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        result = await api_manager.get_exploited_vulnerabilities()
        assert result.list is not None
        assert len(result.list) == 2

    async def test_get_exploited_vulnerabilities_endpoint(
        self, api_manager, httpx_mock, sample_vulnerabilities_list
    ):
        """Test that correct endpoint is called."""
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        await api_manager.get_exploited_vulnerabilities()
        assert "/api/exploitedvulnerabilities" in str(httpx_mock.get_requests()[0].url)

    async def test_get_exploited_vulnerabilities_cached(
        self, api_manager, httpx_mock, sample_vulnerabilities_list
    ):
        """Test that the response is served from cache on repeat calls."""
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        r1 = await api_manager.get_exploited_vulnerabilities()
        r2 = await api_manager.get_exploited_vulnerabilities()
        assert r1 is r2
        assert len(httpx_mock.get_requests()) == 1


class TestGetCriticalVulnerabilities:
    """Test get_critical_vulnerabilities method."""

    async def test_get_critical_vulnerabilities_success(
        self, api_manager, httpx_mock, sample_vulnerabilities_list
    ):
        """Test successful retrieval of critical vulnerabilities."""
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        result = await api_manager.get_critical_vulnerabilities()
        assert result.list is not None
        assert len(result.list) == 2

    async def test_get_critical_vulnerabilities_endpoint(
        self, api_manager, httpx_mock, sample_vulnerabilities_list
    ):
        """Test that correct endpoint is called."""
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        await api_manager.get_critical_vulnerabilities()
        assert "/api/criticalvulnerabilities" in str(httpx_mock.get_requests()[0].url)

    async def test_get_critical_vulnerabilities_cached(
        self, api_manager, httpx_mock, sample_vulnerabilities_list
    ):
        """Test that the response is served from cache on repeat calls."""
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        r1 = await api_manager.get_critical_vulnerabilities()
        r2 = await api_manager.get_critical_vulnerabilities()
        assert r1 is r2
        assert len(httpx_mock.get_requests()) == 1


class TestSearchVulnerabilities:
    """Test search_vulnerabilities method."""

    async def test_search_vulnerabilities_no_filters(
        self, api_manager, httpx_mock, sample_search_response
    ):
        """Test search with no filters."""
        httpx_mock.add_response(json=sample_search_response)
        result = await api_manager.search_vulnerabilities()
        assert isinstance(result, SearchResponse)
        assert result.total_elements == 100

    async def test_search_vulnerabilities_with_score_filter(
        self, api_manager, httpx_mock, sample_search_response
    ):
        """Test search with CVSS score filters."""
        httpx_mock.add_response(json=sample_search_response)
        await api_manager.search_vulnerabilities(from_score=7.5, to_score=10)
        url = str(httpx_mock.get_requests()[0].url)
        assert "fromScore=7.5" in url
        assert "toScore=10" in url

    async def test_search_vulnerabilities_with_epss_filter(
        self, api_manager, httpx_mock, sample_search_response
    ):
        """Test search with EPSS score filters."""
        httpx_mock.add_response(json=sample_search_response)
        await api_manager.search_vulnerabilities(from_epss=50, to_epss=100)
        url = str(httpx_mock.get_requests()[0].url)
        assert "fromEpss=50" in url
        assert "toEpss=100" in url

    async def test_search_vulnerabilities_with_date_filter(
        self, api_manager, httpx_mock, sample_search_response
    ):
        """Test search with date filters."""
        httpx_mock.add_response(json=sample_search_response)
        await api_manager.search_vulnerabilities(
            from_date="2024-01-01", to_date="2024-12-31"
        )
        url = str(httpx_mock.get_requests()[0].url)
        assert "fromDate=2024-01-01" in url
        assert "toDate=2024-12-31" in url

    async def test_search_vulnerabilities_with_text_filter(
        self, api_manager, httpx_mock, sample_search_response
    ):
        """Test search with text/keyword filter."""
        httpx_mock.add_response(json=sample_search_response)
        await api_manager.search_vulnerabilities(text="Windows")
        assert "text=Windows" in str(httpx_mock.get_requests()[0].url)

    async def test_search_vulnerabilities_with_exploited_filter(
        self, api_manager, httpx_mock, sample_search_response
    ):
        """Test search with exploited status filter."""
        httpx_mock.add_response(json=sample_search_response)
        await api_manager.search_vulnerabilities(exploited=True)
        assert "exploited=true" in str(httpx_mock.get_requests()[0].url)

    async def test_search_vulnerabilities_with_pagination(
        self, api_manager, httpx_mock, sample_search_response
    ):
        """Test search with pagination."""
        httpx_mock.add_response(json=sample_search_response)
        await api_manager.search_vulnerabilities(page=1, size=20)
        url = str(httpx_mock.get_requests()[0].url)
        assert "page=1" in url
        assert "size=20" in url

    async def test_search_vulnerabilities_endpoint(
        self, api_manager, httpx_mock, sample_search_response
    ):
        """Test that correct endpoint is called."""
        httpx_mock.add_response(json=sample_search_response)
        await api_manager.search_vulnerabilities()
        assert "/api/search" in str(httpx_mock.get_requests()[0].url)


class TestGetVulnerabilityById:
    """Test get_vulnerability_by_id method."""

    async def test_get_vulnerability_by_id_success(
        self, api_manager, httpx_mock, sample_vulnerability
    ):
        """Test successful retrieval of a vulnerability by ID."""
        httpx_mock.add_response(json=sample_vulnerability)
        result = await api_manager.get_vulnerability_by_id("EUVD-2024-45012")
        assert isinstance(result, Vulnerability)
        assert result.id == "EUVD-2024-45012"

    async def test_get_vulnerability_by_id_endpoint(
        self, api_manager, httpx_mock, sample_vulnerability
    ):
        """Test that correct endpoint is called with ID parameter."""
        httpx_mock.add_response(json=sample_vulnerability)
        await api_manager.get_vulnerability_by_id("EUVD-2024-45012")
        url = str(httpx_mock.get_requests()[0].url)
        assert "/api/enisaid" in url
        assert "id=EUVD-2024-45012" in url

    async def test_get_vulnerability_by_id_not_found(self, api_manager, httpx_mock):
        """Test handling of not-found vulnerability."""
        httpx_mock.add_response(status_code=404)
        with pytest.raises(httpx.HTTPStatusError):
            await api_manager.get_vulnerability_by_id("EUVD-9999-99999")


class TestGetAdvisoryById:
    """Test get_advisory_by_id method."""

    async def test_get_advisory_by_id_success(
        self, api_manager, httpx_mock, sample_advisory
    ):
        """Test successful retrieval of an advisory by ID."""
        httpx_mock.add_response(json=sample_advisory)
        result = await api_manager.get_advisory_by_id("cisco-sa-ata19x-multi-RDTEqRsy")
        assert isinstance(result, Advisory)
        assert result.id == "cisco-sa-ata19x-multi-RDTEqRsy"

    async def test_get_advisory_by_id_endpoint(
        self, api_manager, httpx_mock, sample_advisory
    ):
        """Test that correct endpoint is called with advisory ID parameter."""
        httpx_mock.add_response(json=sample_advisory)
        await api_manager.get_advisory_by_id("test-advisory-001")
        url = str(httpx_mock.get_requests()[0].url)
        assert "/api/advisory" in url
        assert "id=test-advisory-001" in url


class TestAsyncContextManager:
    """Test EUVDAPIManager as an async context manager."""

    async def test_context_manager_enter(self):
        """Test entering async context manager."""
        async with EUVDAPIManager() as manager:
            assert manager is not None

    async def test_context_manager_closes_client(self):
        """Test that client is closed on context manager exit."""
        async with EUVDAPIManager() as manager:
            _ = manager._get_client()  # force client creation
            assert manager._client is not None
        assert manager._client is None

    async def test_close_method(self, api_manager):
        """Test close method releases the client."""
        _ = api_manager._get_client()
        await api_manager.close()
        assert api_manager._client is None


class TestRetryBehavior:
    """Test retry logic in _make_request."""

    async def test_retries_on_retryable_status(self, httpx_mock):
        """Test that retryable status codes trigger a retry."""
        manager = EUVDAPIManager(timeout=10, max_retries=1, cache_ttl=0)
        httpx_mock.add_response(status_code=503)
        httpx_mock.add_response(json={"ok": True})
        result = await manager._make_request("/api/test")
        assert result == {"ok": True}
        assert len(httpx_mock.get_requests()) == 2

    async def test_no_retry_on_client_error(self, httpx_mock):
        """Test that 4xx client errors are not retried."""
        manager = EUVDAPIManager(timeout=10, max_retries=2, cache_ttl=0)
        httpx_mock.add_response(status_code=400)
        with pytest.raises(httpx.HTTPStatusError):
            await manager._make_request("/api/test")
        assert len(httpx_mock.get_requests()) == 1

    async def test_retries_on_transport_error(self, httpx_mock):
        """Test that transport errors are retried."""
        manager = EUVDAPIManager(timeout=10, max_retries=1, cache_ttl=0)
        httpx_mock.add_exception(httpx.ConnectError("refused"))
        httpx_mock.add_response(json={"ok": True})
        result = await manager._make_request("/api/test")
        assert result == {"ok": True}

    async def test_raises_after_all_retries_exhausted(self, httpx_mock):
        """Test that exception is raised after all retries are exhausted."""
        manager = EUVDAPIManager(timeout=10, max_retries=1, cache_ttl=0)
        httpx_mock.add_exception(httpx.ConnectError("refused"))
        httpx_mock.add_exception(httpx.ConnectError("refused"))
        with pytest.raises(httpx.TransportError):
            await manager._make_request("/api/test")
        assert len(httpx_mock.get_requests()) == 2
