"""
Integration tests for EUVD MCP Server.

These tests verify that different components work together correctly.
"""

from unittest.mock import Mock

import pytest

from euvd_mcp.models import SearchResponse, Vulnerability


@pytest.mark.integration
class TestAPIManagerIntegration:
    """Integration tests for API manager with mocked HTTP responses."""

    def test_search_and_parse_vulnerabilities(self, api_manager, mock_requests_get, sample_search_response):
        """Test searching and parsing vulnerability data."""
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        # Search for vulnerabilities
        result = api_manager.search_vulnerabilities(from_score=8.0)

        # Verify results are properly parsed
        assert isinstance(result, SearchResponse)
        assert result.total_elements == 100
        assert len(result.content) == 2

        # Verify vulnerabilities are properly deserialized
        for vuln in result.content:
            assert isinstance(vuln, Vulnerability)
            assert vuln.id is not None

    def test_get_vulnerability_details_flow(self, api_manager, mock_requests_get, sample_vulnerability):
        """Test getting a vulnerability and accessing its details."""
        mock_response = Mock()
        mock_response.json.return_value = sample_vulnerability
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        # Get specific vulnerability
        vuln = api_manager.get_vulnerability_by_id("EUVD-2024-45012")

        # Verify all fields are accessible
        assert vuln.id == "EUVD-2024-45012"
        assert vuln.base_score == 8.5
        assert vuln.assigner == "mitre"
        assert vuln.epss == 45.5
        assert vuln.description is not None

    def test_multiple_search_queries(self, api_manager, mock_requests_get, sample_search_response):
        """Test making multiple search queries."""
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        # First search
        result1 = api_manager.search_vulnerabilities(from_score=7.0, to_score=8.0)
        assert len(result1.content) == 2

        # Second search with different parameters
        result2 = api_manager.search_vulnerabilities(vendor="Microsoft")
        assert len(result2.content) == 2

        # Verify both calls were made
        assert mock_requests_get.call_count == 2

    def test_last_vulnerabilities_flow(self, api_manager, mock_requests_get, sample_vulnerabilities_list):
        """Test the complete flow of getting last vulnerabilities."""
        mock_response = Mock()
        mock_response.json.return_value = sample_vulnerabilities_list
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        result = api_manager.get_last_vulnerabilities()

        # Verify response structure
        assert result.list is not None
        assert len(result.list) == 2
        assert all(isinstance(v, Vulnerability) for v in result.list)

    def test_exploited_vulnerabilities_flow(self, api_manager, mock_requests_get, sample_vulnerabilities_list):
        """Test the complete flow of getting exploited vulnerabilities."""
        mock_response = Mock()
        mock_response.json.return_value = sample_vulnerabilities_list
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        result = api_manager.get_exploited_vulnerabilities()

        # Verify response structure
        assert result.list is not None
        assert len(result.list) == 2
        assert all(isinstance(v, Vulnerability) for v in result.list)

    def test_critical_vulnerabilities_flow(self, api_manager, mock_requests_get, sample_vulnerabilities_list):
        """Test the complete flow of getting critical vulnerabilities."""
        mock_response = Mock()
        mock_response.json.return_value = sample_vulnerabilities_list
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        result = api_manager.get_critical_vulnerabilities()

        # Verify response structure
        assert result.list is not None
        assert len(result.list) == 2
        assert all(isinstance(v, Vulnerability) for v in result.list)


@pytest.mark.integration
class TestDataSerialization:
    """Integration tests for data serialization and deserialization."""

    def test_vulnerability_round_trip(self, sample_vulnerability):
        """Test that vulnerability can be serialized and deserialized."""
        # Deserialize from dict
        vuln = Vulnerability.model_validate(sample_vulnerability)

        # Serialize back to dict
        serialized = vuln.model_dump(mode="json", by_alias=True)

        # Verify all fields are present
        assert serialized["id"] == sample_vulnerability["id"]
        assert serialized["baseScore"] == sample_vulnerability["baseScore"]
        assert serialized["description"] == sample_vulnerability["description"]

    def test_search_response_round_trip(self, sample_search_response):
        """Test that search response can be serialized and deserialized."""
        # Deserialize from dict
        response = SearchResponse.model_validate(sample_search_response)

        # Serialize back to dict
        serialized = response.model_dump(mode="json", by_alias=True)

        # Verify structure is preserved
        assert "content" in serialized
        assert len(serialized["content"]) == 2
        assert serialized["totalElements"] == 100

    def test_json_compatibility(self, sample_vulnerability):
        """Test that serialized data is JSON-compatible."""
        import json

        vuln = Vulnerability.model_validate(sample_vulnerability)
        serialized = vuln.model_dump(mode="json")

        # Should be JSON serializable
        json_str = json.dumps(serialized)
        deserialized = json.loads(json_str)

        # Should be able to recreate model
        vuln2 = Vulnerability.model_validate(deserialized)
        assert vuln2.id == vuln.id


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling across components."""

    def test_api_error_propagation(self, api_manager, mock_requests_get):
        """Test that API errors are properly propagated."""
        import requests

        mock_requests_get.side_effect = requests.exceptions.RequestException("API Error")

        with pytest.raises(requests.exceptions.RequestException):
            api_manager.search_vulnerabilities()

    def test_invalid_response_handling(self, api_manager, mock_requests_get):
        """Test handling of invalid API responses."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_requests_get.return_value = mock_response

        with pytest.raises(ValueError):
            api_manager._make_request("/api/test")

    def test_validation_error_handling(self, api_manager, mock_requests_get):
        """Test handling of validation errors."""
        mock_response = Mock()
        # Return valid but minimal data
        mock_response.json.return_value = {"id": "test"}
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        # Should successfully parse even with minimal data
        result = api_manager.get_advisory_by_id("test")
        assert result.id == "test"


@pytest.mark.integration
class TestComplexScenarios:
    """Integration tests for complex real-world scenarios."""

    def test_pagination_scenario(self, api_manager, mock_requests_get):
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

        # Mock responses for two consecutive calls
        mock_response_0 = Mock()
        mock_response_0.json.return_value = page_0_response
        mock_response_0.raise_for_status = Mock()

        mock_response_1 = Mock()
        mock_response_1.json.return_value = page_1_response
        mock_response_1.raise_for_status = Mock()

        mock_requests_get.side_effect = [mock_response_0, mock_response_1]

        # Get first page
        result_0 = api_manager.search_vulnerabilities(page=0, size=10)
        assert result_0.page == 0
        assert len(result_0.content) == 10

        # Get second page
        result_1 = api_manager.search_vulnerabilities(page=1, size=10)
        assert result_1.page == 1
        assert len(result_1.content) == 10

        # Verify different results
        assert result_0.content[0].id != result_1.content[0].id

    def test_filter_combination_scenario(self, api_manager, mock_requests_get, sample_search_response):
        """Test applying multiple filters in a single search."""
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        # Complex search with multiple filters
        api_manager.search_vulnerabilities(
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

        # Verify all filters were sent
        call_args = mock_requests_get.call_args
        params = call_args.kwargs["params"]

        assert params["fromScore"] == 7.5
        assert params["toScore"] == 10
        assert params["fromEpss"] == 50
        assert params["toEpss"] == 100
        assert params["vendor"] == "Microsoft"
        assert params["product"] == "Windows"
        assert params["exploited"] == "true"
        assert params["page"] == 0
        assert params["size"] == 20

    def test_vulnerability_detail_retrieval_scenario(self, api_manager, mock_requests_get):
        """Test retrieving details after searching."""
        # Mock search response
        search_response = {
            "content": [{"id": "EUVD-2024-45012"}, {"id": "EUVD-2024-45013"}],
            "totalElements": 2,
            "totalPages": 1,
            "page": 0,
            "size": 10,
        }

        # Mock detail response
        detail_response = {
            "id": "EUVD-2024-45012",
            "description": "Detailed vulnerability information",
            "baseScore": 9.0,
            "epss": 75.0,
            "assigner": "mitre",
        }

        # Setup mock to return different responses
        search_mock = Mock()
        search_mock.json.return_value = search_response
        search_mock.raise_for_status = Mock()

        detail_mock = Mock()
        detail_mock.json.return_value = detail_response
        detail_mock.raise_for_status = Mock()

        mock_requests_get.side_effect = [search_mock, detail_mock]

        # First, search for vulnerabilities
        search_result = api_manager.search_vulnerabilities()
        first_vuln_id = search_result.content[0].id

        # Then get details of first vulnerability
        detail = api_manager.get_vulnerability_by_id(first_vuln_id)

        assert detail.id == "EUVD-2024-45012"
        assert detail.description == "Detailed vulnerability information"
        assert detail.base_score == 9.0
