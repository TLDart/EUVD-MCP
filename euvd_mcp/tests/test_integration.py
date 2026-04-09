"""
Integration tests for EUVD MCP Server.

These tests verify that different components work together correctly.
"""

import json

import httpx
import pytest

from euvd_mcp.models import SearchResponse, Vulnerability


@pytest.mark.integration
class TestAPIManagerIntegration:
    """Integration tests for API manager with mocked HTTP responses."""

    async def test_search_and_parse_vulnerabilities(
        self, api_manager, httpx_mock, sample_search_response
    ):
        """Test searching and parsing vulnerability data."""
        httpx_mock.add_response(json=sample_search_response)
        result = await api_manager.search_vulnerabilities(from_score=8.0)
        assert isinstance(result, SearchResponse)
        assert result.total_elements == 100
        assert len(result.content) == 2
        for vuln in result.content:
            assert isinstance(vuln, Vulnerability)
            assert vuln.id is not None

    async def test_get_vulnerability_details_flow(
        self, api_manager, httpx_mock, sample_vulnerability
    ):
        """Test getting a vulnerability and accessing its details."""
        httpx_mock.add_response(json=sample_vulnerability)
        vuln = await api_manager.get_vulnerability_by_id("EUVD-2024-45012")
        assert vuln.id == "EUVD-2024-45012"
        assert vuln.base_score == 8.5
        assert vuln.assigner == "mitre"
        assert vuln.epss == 45.5
        assert vuln.description is not None

    async def test_multiple_search_queries(
        self, api_manager, httpx_mock, sample_search_response
    ):
        """Test making multiple search queries."""
        httpx_mock.add_response(json=sample_search_response)
        httpx_mock.add_response(json=sample_search_response)
        result1 = await api_manager.search_vulnerabilities(from_score=7.0, to_score=8.0)
        result2 = await api_manager.search_vulnerabilities(vendor="Microsoft")
        assert len(result1.content) == 2
        assert len(result2.content) == 2
        assert len(httpx_mock.get_requests()) == 2

    async def test_last_vulnerabilities_flow(
        self, api_manager, httpx_mock, sample_vulnerabilities_list
    ):
        """Test the complete flow of getting last vulnerabilities."""
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        result = await api_manager.get_last_vulnerabilities()
        assert result.list is not None
        assert len(result.list) == 2
        assert all(isinstance(v, Vulnerability) for v in result.list)

    async def test_exploited_vulnerabilities_flow(
        self, api_manager, httpx_mock, sample_vulnerabilities_list
    ):
        """Test the complete flow of getting exploited vulnerabilities."""
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        result = await api_manager.get_exploited_vulnerabilities()
        assert result.list is not None
        assert len(result.list) == 2
        assert all(isinstance(v, Vulnerability) for v in result.list)

    async def test_critical_vulnerabilities_flow(
        self, api_manager, httpx_mock, sample_vulnerabilities_list
    ):
        """Test the complete flow of getting critical vulnerabilities."""
        httpx_mock.add_response(json=sample_vulnerabilities_list)
        result = await api_manager.get_critical_vulnerabilities()
        assert result.list is not None
        assert len(result.list) == 2
        assert all(isinstance(v, Vulnerability) for v in result.list)


@pytest.mark.integration
class TestDataSerialization:
    """Integration tests for data serialization and deserialization."""

    def test_vulnerability_round_trip(self, sample_vulnerability):
        """Test that vulnerability can be serialized and deserialized."""
        vuln = Vulnerability.model_validate(sample_vulnerability)
        serialized = vuln.model_dump(mode="json", by_alias=True)
        assert serialized["id"] == sample_vulnerability["id"]
        assert serialized["baseScore"] == sample_vulnerability["baseScore"]
        assert serialized["description"] == sample_vulnerability["description"]

    def test_search_response_round_trip(self, sample_search_response):
        """Test that search response can be serialized and deserialized."""
        response = SearchResponse.model_validate(sample_search_response)
        serialized = response.model_dump(mode="json", by_alias=True)
        assert "content" in serialized
        assert len(serialized["content"]) == 2
        assert serialized["totalElements"] == 100

    def test_json_compatibility(self, sample_vulnerability):
        """Test that serialized data is JSON-compatible."""
        vuln = Vulnerability.model_validate(sample_vulnerability)
        serialized = vuln.model_dump(mode="json")
        json_str = json.dumps(serialized)
        deserialized = json.loads(json_str)
        vuln2 = Vulnerability.model_validate(deserialized)
        assert vuln2.id == vuln.id


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling across components."""

    async def test_api_error_propagation(self, api_manager, httpx_mock):
        """Test that HTTP errors are properly propagated."""
        httpx_mock.add_exception(httpx.ConnectError("API Error"))
        with pytest.raises(httpx.TransportError):
            await api_manager.search_vulnerabilities()

    async def test_http_status_error_propagation(self, api_manager, httpx_mock):
        """Test that non-retryable HTTP status errors propagate."""
        httpx_mock.add_response(status_code=404)
        with pytest.raises(httpx.HTTPStatusError):
            await api_manager._make_request("/api/test")

    async def test_validation_error_handling(self, api_manager, httpx_mock):
        """Test handling of valid but minimal API responses."""
        httpx_mock.add_response(json={"id": "test"})
        result = await api_manager.get_advisory_by_id("test")
        assert result.id == "test"


@pytest.mark.integration
class TestComplexScenarios:
    """Integration tests for complex real-world scenarios."""

    async def test_pagination_scenario(self, api_manager, httpx_mock):
        """Test simulating pagination through results."""
        page_0_response = {
            "content": [{"id": f"EUVD-2024-{i:05d}"} for i in range(10)],
            "totalElements": 50,
            "totalPages": 5,
            "page": 0,
            "size": 10,
        }
        page_1_response = {
            "content": [{"id": f"EUVD-2024-{i:05d}"} for i in range(10, 20)],
            "totalElements": 50,
            "totalPages": 5,
            "page": 1,
            "size": 10,
        }
        httpx_mock.add_response(json=page_0_response)
        httpx_mock.add_response(json=page_1_response)

        result_0 = await api_manager.search_vulnerabilities(page=0, size=10)
        assert result_0.page == 0
        assert len(result_0.content) == 10

        result_1 = await api_manager.search_vulnerabilities(page=1, size=10)
        assert result_1.page == 1
        assert len(result_1.content) == 10

        assert result_0.content[0].id != result_1.content[0].id

    async def test_filter_combination_scenario(
        self, api_manager, httpx_mock, sample_search_response
    ):
        """Test applying multiple filters in a single search."""
        httpx_mock.add_response(json=sample_search_response)
        await api_manager.search_vulnerabilities(
            from_score=7.5,
            to_score=10,
            from_epss=50,
            to_epss=100,
            vendor="Microsoft",
            product="Windows",
            exploited=True,
            page=0,
            size=20,
        )
        url = str(httpx_mock.get_requests()[0].url)
        assert "fromScore=7.5" in url
        assert "toScore=10" in url
        assert "fromEpss=50" in url
        assert "toEpss=100" in url
        assert "vendor=Microsoft" in url
        assert "product=Windows" in url
        assert "exploited=true" in url
        assert "page=0" in url
        assert "size=20" in url

    async def test_vulnerability_detail_retrieval_scenario(
        self, api_manager, httpx_mock
    ):
        """Test retrieving details after searching."""
        search_response = {
            "content": [{"id": "EUVD-2024-45012"}, {"id": "EUVD-2024-45013"}],
            "totalElements": 2,
            "totalPages": 1,
            "page": 0,
            "size": 10,
        }
        detail_response = {
            "id": "EUVD-2024-45012",
            "description": "Detailed vulnerability information",
            "baseScore": 9.0,
            "epss": 75.0,
            "assigner": "mitre",
        }
        httpx_mock.add_response(json=search_response)
        httpx_mock.add_response(json=detail_response)

        search_result = await api_manager.search_vulnerabilities()
        first_vuln_id = search_result.content[0].id

        detail = await api_manager.get_vulnerability_by_id(first_vuln_id)
        assert detail.id == "EUVD-2024-45012"
        assert detail.description == "Detailed vulnerability information"
        assert detail.base_score == 9.0
