"""
Unit tests for Pydantic models.
"""

from euvd_mcp.models import (
    Advisory,
    ExploitedVulnerabilities,
    SearchResponse,
    Vulnerability,
    VulnerabilityListResponse,
)


class TestVulnerabilityModel:
    """Test the Vulnerability model."""

    def test_vulnerability_creation(self, sample_vulnerability):
        """Test creating a Vulnerability from a dict."""
        vuln = Vulnerability.model_validate(sample_vulnerability)
        assert vuln.id == "EUVD-2024-45012"
        assert vuln.base_score == 8.5
        assert vuln.assigner == "mitre"

    def test_vulnerability_with_minimal_fields(self):
        """Test Vulnerability with only required fields."""
        minimal_data = {"id": "EUVD-2024-45012"}
        vuln = Vulnerability.model_validate(minimal_data)
        assert vuln.id == "EUVD-2024-45012"
        assert vuln.base_score is None
        assert vuln.description is None

    def test_vulnerability_json_serialization(self, sample_vulnerability):
        """Test serializing Vulnerability to JSON."""
        vuln = Vulnerability.model_validate(sample_vulnerability)
        json_data = vuln.model_dump(mode="json", by_alias=True)
        assert json_data["id"] == "EUVD-2024-45012"
        assert json_data["baseScore"] == 8.5

    def test_vulnerability_alias_fields(self, sample_vulnerability):
        """Test that field aliases work correctly."""
        vuln = Vulnerability.model_validate(sample_vulnerability)
        assert vuln.date_published == "2024-01-01T00:00:00Z"
        assert vuln.base_score_version == "3.1"
        assert vuln.base_score_vector == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"

    def test_vulnerability_extra_fields_allowed(self, sample_vulnerability):
        """Test that extra fields are allowed and preserved."""
        sample_vulnerability["custom_field"] = "custom_value"
        vuln = Vulnerability.model_validate(sample_vulnerability)
        assert vuln.id == "EUVD-2024-45012"


class TestVulnerabilityListResponse:
    """Test the VulnerabilityListResponse model."""

    def test_vulnerability_list_creation(self, sample_vulnerabilities_list):
        """Test creating a VulnerabilityListResponse."""
        response = VulnerabilityListResponse.model_validate(sample_vulnerabilities_list)
        assert len(response) == 2
        assert response.root[0].id == "EUVD-2024-45012"
        assert response.root[1].id == "EUVD-2024-45013"

    def test_vulnerability_list_iteration(self, sample_vulnerabilities_list):
        """Test iterating over VulnerabilityListResponse."""
        response = VulnerabilityListResponse.model_validate(sample_vulnerabilities_list)
        ids = [v.id for v in response]
        assert len(ids) == 2
        assert "EUVD-2024-45012" in ids

    def test_vulnerability_list_empty(self):
        """Test creating an empty VulnerabilityListResponse."""
        response = VulnerabilityListResponse.model_validate([])
        assert len(response) == 0

    def test_vulnerabilities_property(self, sample_vulnerabilities_list):
        """Test the vulnerabilities property."""
        response = VulnerabilityListResponse.model_validate(sample_vulnerabilities_list)
        vulns = response.vulnerabilities
        assert len(vulns) == 2
        assert all(isinstance(v, Vulnerability) for v in vulns)


class TestExploitedVulnerabilities:
    """Test the ExploitedVulnerabilities model."""

    def test_exploited_vulnerabilities_creation(self, sample_vulnerabilities_list):
        """Test creating an ExploitedVulnerabilities response."""
        response = ExploitedVulnerabilities(list=sample_vulnerabilities_list)
        assert len(response.list) == 2

    def test_exploited_vulnerabilities_validation(self, sample_vulnerabilities_list):
        """Test validating data for ExploitedVulnerabilities."""
        data = {"list": sample_vulnerabilities_list}
        response = ExploitedVulnerabilities.model_validate(data)
        assert len(response.list) == 2
        assert response.list[0].id == "EUVD-2024-45012"

    def test_exploited_vulnerabilities_json_serialization(self, sample_vulnerabilities_list):
        """Test serializing ExploitedVulnerabilities to JSON."""
        response = ExploitedVulnerabilities(list=sample_vulnerabilities_list)
        json_data = response.model_dump(mode="json")
        assert "list" in json_data
        assert len(json_data["list"]) == 2


class TestSearchResponse:
    """Test the SearchResponse model."""

    def test_search_response_creation(self, sample_search_response):
        """Test creating a SearchResponse."""
        response = SearchResponse.model_validate(sample_search_response)
        assert response.total_elements == 100
        assert response.total_pages == 10
        assert response.page == 0
        assert response.size == 10
        assert len(response.content) == 2

    def test_search_response_iteration(self, sample_search_response):
        """Test iterating over SearchResponse."""
        response = SearchResponse.model_validate(sample_search_response)
        ids = [v.id for v in response]
        assert len(ids) == 2

    def test_search_response_len(self, sample_search_response):
        """Test len() on SearchResponse."""
        response = SearchResponse.model_validate(sample_search_response)
        assert len(response) == 2

    def test_search_response_alternative_field_names(self, sample_search_response):
        """Test that alternative field names work."""
        # Test with 'data' field instead of 'content'
        data_response = {
            "data": sample_search_response["content"],
            "total": 100,
            "totalPages": 10,
            "page": 0,
            "size": 10,
        }
        response = SearchResponse.model_validate(data_response)
        assert len(response) == 2

    def test_search_response_no_results(self):
        """Test SearchResponse with no results."""
        data = {
            "content": [],
            "totalElements": 0,
            "totalPages": 0,
            "page": 0,
            "size": 10,
        }
        response = SearchResponse.model_validate(data)
        assert len(response) == 0
        assert response.total_elements == 0


class TestAdvisoryModel:
    """Test the Advisory model."""

    def test_advisory_creation(self, sample_advisory):
        """Test creating an Advisory from a dict."""
        advisory = Advisory.model_validate(sample_advisory)
        assert advisory.id == "cisco-sa-ata19x-multi-RDTEqRsy"
        assert advisory.base_score == 7.5
        assert advisory.source.name == "Cisco"

    def test_advisory_with_minimal_fields(self):
        """Test Advisory with only required fields."""
        minimal_data = {"id": "test-advisory-001"}
        advisory = Advisory.model_validate(minimal_data)
        assert advisory.id == "test-advisory-001"
        assert advisory.description is None
        assert advisory.source is None

    def test_advisory_json_serialization(self, sample_advisory):
        """Test serializing Advisory to JSON."""
        advisory = Advisory.model_validate(sample_advisory)
        json_data = advisory.model_dump(mode="json", by_alias=True)
        assert json_data["id"] == "cisco-sa-ata19x-multi-RDTEqRsy"
        assert json_data["baseScore"] == 7.5

    def test_advisory_source_nested(self, sample_advisory):
        """Test that nested source object is properly deserialized."""
        advisory = Advisory.model_validate(sample_advisory)
        assert advisory.source is not None
        assert advisory.source.id == 1
        assert advisory.source.name == "Cisco"
