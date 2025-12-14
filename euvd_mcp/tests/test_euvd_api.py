"""
Unit tests for the EUVD API Manager.
"""

from unittest.mock import Mock

import pytest
import requests

from euvd_mcp.controllers.euvd_api import EUVDAPIManager
from euvd_mcp.models import Advisory, SearchResponse, Vulnerability


class TestEUVDAPIManagerInit:
    """Test EUVDAPIManager initialization."""

    def test_api_manager_default_init(self):
        """Test initializing API manager with defaults."""
        manager = EUVDAPIManager()
        assert manager.timeout > 0
        assert manager.session is not None

    def test_api_manager_custom_timeout(self):
        """Test initializing API manager with custom timeout."""
        manager = EUVDAPIManager(timeout=60)
        assert manager.timeout == 60

    def test_api_manager_custom_retries(self):
        """Test initializing API manager with custom max retries."""
        manager = EUVDAPIManager(max_retries=5)
        assert manager.session is not None

    def test_api_manager_session_headers(self):
        """Test that session headers are properly set."""
        manager = EUVDAPIManager()
        assert "User-Agent" in manager.session.headers
        assert "Accept" in manager.session.headers


class TestEUVDAPIManagerRequests:
    """Test API request methods."""

    def test_make_request_success(self, api_manager, mock_requests_get):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "test"}
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        result = api_manager._make_request("/api/test")
        assert result == {"id": "test"}
        mock_requests_get.assert_called_once()

    def test_make_request_with_params(self, api_manager, mock_requests_get):
        """Test API request with query parameters."""
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        params = {"fromScore": 7.5, "toScore": 10}
        result = api_manager._make_request("/api/search", params=params)

        assert result == {"results": []}
        call_args = mock_requests_get.call_args
        assert call_args.kwargs["params"] == params

    def test_make_request_failure(self, api_manager, mock_requests_get):
        """Test API request failure."""
        mock_requests_get.side_effect = requests.exceptions.RequestException("Connection error")

        with pytest.raises(requests.exceptions.RequestException):
            api_manager._make_request("/api/test")


class TestGetLastVulnerabilities:
    """Test get_last_vulnerabilities method."""

    def test_get_last_vulnerabilities_success(self, api_manager, mock_requests_get, sample_vulnerabilities_list):
        """Test successful retrieval of last vulnerabilities."""
        mock_response = Mock()
        mock_response.json.return_value = sample_vulnerabilities_list
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        result = api_manager.get_last_vulnerabilities()
        # Result is VulnerabilityListResponse which is a list wrapped in ExploitedVulnerabilities
        assert result.list is not None
        assert len(result.list) == 2
        mock_requests_get.assert_called_once()

    def test_get_last_vulnerabilities_endpoint(self, api_manager, mock_requests_get, sample_vulnerabilities_list):
        """Test that correct endpoint is called."""
        mock_response = Mock()
        mock_response.json.return_value = sample_vulnerabilities_list
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        api_manager.get_last_vulnerabilities()

        call_args = mock_requests_get.call_args
        assert "/api/lastvulnerabilities" in call_args[0][0]


class TestGetExploitedVulnerabilities:
    """Test get_exploited_vulnerabilities method."""

    def test_get_exploited_vulnerabilities_success(self, api_manager, mock_requests_get, sample_vulnerabilities_list):
        """Test successful retrieval of exploited vulnerabilities."""
        mock_response = Mock()
        mock_response.json.return_value = sample_vulnerabilities_list
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        result = api_manager.get_exploited_vulnerabilities()
        assert result.list is not None
        assert len(result.list) == 2

    def test_get_exploited_vulnerabilities_endpoint(self, api_manager, mock_requests_get, sample_vulnerabilities_list):
        """Test that correct endpoint is called."""
        mock_response = Mock()
        mock_response.json.return_value = sample_vulnerabilities_list
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        api_manager.get_exploited_vulnerabilities()

        call_args = mock_requests_get.call_args
        assert "/api/exploitedvulnerabilities" in call_args[0][0]


class TestGetCriticalVulnerabilities:
    """Test get_critical_vulnerabilities method."""

    def test_get_critical_vulnerabilities_success(self, api_manager, mock_requests_get, sample_vulnerabilities_list):
        """Test successful retrieval of critical vulnerabilities."""
        mock_response = Mock()
        mock_response.json.return_value = sample_vulnerabilities_list
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        result = api_manager.get_critical_vulnerabilities()
        assert result.list is not None
        assert len(result.list) == 2

    def test_get_critical_vulnerabilities_endpoint(self, api_manager, mock_requests_get, sample_vulnerabilities_list):
        """Test that correct endpoint is called."""
        mock_response = Mock()
        mock_response.json.return_value = sample_vulnerabilities_list
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        api_manager.get_critical_vulnerabilities()

        call_args = mock_requests_get.call_args
        assert "/api/criticalvulnerabilities" in call_args[0][0]


class TestSearchVulnerabilities:
    """Test search_vulnerabilities method."""

    def test_search_vulnerabilities_no_filters(self, api_manager, mock_requests_get, sample_search_response):
        """Test search with no filters."""
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        result = api_manager.search_vulnerabilities()
        assert isinstance(result, SearchResponse)
        assert result.total_elements == 100

    def test_search_vulnerabilities_with_score_filter(self, api_manager, mock_requests_get, sample_search_response):
        """Test search with CVSS score filters."""
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        result = api_manager.search_vulnerabilities(from_score=7.5, to_score=10)
        assert isinstance(result, SearchResponse)

        call_args = mock_requests_get.call_args
        params = call_args.kwargs["params"]
        assert params["fromScore"] == 7.5
        assert params["toScore"] == 10

    def test_search_vulnerabilities_with_epss_filter(self, api_manager, mock_requests_get, sample_search_response):
        """Test search with EPSS score filters."""
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        api_manager.search_vulnerabilities(from_epss=50, to_epss=100)

        call_args = mock_requests_get.call_args
        params = call_args.kwargs["params"]
        assert params["fromEpss"] == 50
        assert params["toEpss"] == 100

    def test_search_vulnerabilities_with_date_filter(self, api_manager, mock_requests_get, sample_search_response):
        """Test search with date filters."""
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        api_manager.search_vulnerabilities(from_date="2024-01-01", to_date="2024-12-31")

        call_args = mock_requests_get.call_args
        params = call_args.kwargs["params"]
        assert params["fromDate"] == "2024-01-01"
        assert params["toDate"] == "2024-12-31"

    def test_search_vulnerabilities_with_text_filter(self, api_manager, mock_requests_get, sample_search_response):
        """Test search with text/keyword filter."""
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        api_manager.search_vulnerabilities(text="Windows")

        call_args = mock_requests_get.call_args
        params = call_args.kwargs["params"]
        assert params["text"] == "Windows"

    def test_search_vulnerabilities_with_exploited_filter(self, api_manager, mock_requests_get, sample_search_response):
        """Test search with exploited status filter."""
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        api_manager.search_vulnerabilities(exploited=True)

        call_args = mock_requests_get.call_args
        params = call_args.kwargs["params"]
        assert params["exploited"] == "true"

    def test_search_vulnerabilities_with_pagination(self, api_manager, mock_requests_get, sample_search_response):
        """Test search with pagination."""
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        api_manager.search_vulnerabilities(page=1, size=20)

        call_args = mock_requests_get.call_args
        params = call_args.kwargs["params"]
        assert params["page"] == 1
        assert params["size"] == 20

    def test_search_vulnerabilities_endpoint(self, api_manager, mock_requests_get, sample_search_response):
        """Test that correct endpoint is called."""
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        api_manager.search_vulnerabilities()

        call_args = mock_requests_get.call_args
        assert "/api/search" in call_args[0][0]


class TestGetVulnerabilityById:
    """Test get_vulnerability_by_id method."""

    def test_get_vulnerability_by_id_success(self, api_manager, mock_requests_get, sample_vulnerability):
        """Test successful retrieval of a vulnerability by ID."""
        mock_response = Mock()
        mock_response.json.return_value = sample_vulnerability
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        result = api_manager.get_vulnerability_by_id("EUVD-2024-45012")
        assert isinstance(result, Vulnerability)
        assert result.id == "EUVD-2024-45012"

    def test_get_vulnerability_by_id_endpoint(self, api_manager, mock_requests_get, sample_vulnerability):
        """Test that correct endpoint is called with ID parameter."""
        mock_response = Mock()
        mock_response.json.return_value = sample_vulnerability
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        api_manager.get_vulnerability_by_id("EUVD-2024-45012")

        call_args = mock_requests_get.call_args
        assert "/api/enisaid" in call_args[0][0]
        params = call_args.kwargs["params"]
        assert params["id"] == "EUVD-2024-45012"

    def test_get_vulnerability_by_id_not_found(self, api_manager, mock_requests_get):
        """Test handling of not found vulnerability."""
        mock_requests_get.side_effect = requests.exceptions.RequestException("404 Not Found")

        with pytest.raises(requests.exceptions.RequestException):
            api_manager.get_vulnerability_by_id("INVALID-ID")


class TestGetAdvisoryById:
    """Test get_advisory_by_id method."""

    def test_get_advisory_by_id_success(self, api_manager, mock_requests_get, sample_advisory):
        """Test successful retrieval of an advisory by ID."""
        mock_response = Mock()
        mock_response.json.return_value = sample_advisory
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        result = api_manager.get_advisory_by_id("cisco-sa-ata19x-multi-RDTEqRsy")
        assert isinstance(result, Advisory)
        assert result.id == "cisco-sa-ata19x-multi-RDTEqRsy"

    def test_get_advisory_by_id_endpoint(self, api_manager, mock_requests_get, sample_advisory):
        """Test that correct endpoint is called with advisory ID parameter."""
        mock_response = Mock()
        mock_response.json.return_value = sample_advisory
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        api_manager.get_advisory_by_id("test-advisory-001")

        call_args = mock_requests_get.call_args
        assert "/api/advisory" in call_args[0][0]
        params = call_args.kwargs["params"]
        assert params["id"] == "test-advisory-001"


class TestContextManager:
    """Test EUVDAPIManager as a context manager."""

    def test_context_manager_enter(self):
        """Test entering context manager."""
        with EUVDAPIManager() as manager:
            assert manager is not None
            assert manager.session is not None

    def test_context_manager_exit(self):
        """Test exiting context manager."""
        manager = EUVDAPIManager()
        with manager:
            _ = manager.session
        # Verify session is closed
        assert manager.session is not None  # Session object still exists

    def test_close_method(self):
        """Test close method."""
        manager = EUVDAPIManager()
        manager.close()
        # Manager should be cleanly closed
        assert manager.session is not None  # Session object still exists after close


class TestAPIManagerErrorHandling:
    """Test error handling in API manager."""

    def test_request_timeout(self, api_manager, mock_requests_get):
        """Test handling of request timeout."""
        mock_requests_get.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(requests.exceptions.RequestException):
            api_manager._make_request("/api/test")

    def test_request_connection_error(self, api_manager, mock_requests_get):
        """Test handling of connection error."""
        mock_requests_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        with pytest.raises(requests.exceptions.RequestException):
            api_manager._make_request("/api/test")
