"""
Pytest configuration file.

Defines fixtures and configuration for all tests.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from euvd_mcp.controllers.euvd_api import EUVDAPIManager


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def env_file_path(project_root):
    """Return the path to the .env file."""
    return project_root / ".env"


@pytest.fixture
def sample_vulnerability():
    """Return a sample vulnerability response."""
    return {
        "id": "EUVD-2024-45012",
        "enisaUuid": "uuid-12345",
        "description": "Test vulnerability description",
        "datePublished": "2024-01-01T00:00:00Z",
        "dateUpdated": "2024-12-13T00:00:00Z",
        "baseScore": 8.5,
        "baseScoreVersion": "3.1",
        "baseScoreVector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
        "references": "https://example.com/ref1\nhttps://example.com/ref2",
        "aliases": "CVE-2024-12345",
        "assigner": "mitre",
        "epss": 45.5,
        "enisaIdProduct": [],
        "enisaIdVendor": [],
        "enisaIdVulnerability": [],
        "enisaIdAdvisory": [],
    }


@pytest.fixture
def sample_vulnerabilities_list(sample_vulnerability):
    """Return a sample list of vulnerabilities."""
    vuln1 = sample_vulnerability.copy()
    vuln2 = sample_vulnerability.copy()
    vuln2["id"] = "EUVD-2024-45013"
    vuln2["aliases"] = "CVE-2024-12346"
    return [vuln1, vuln2]


@pytest.fixture
def sample_search_response(sample_vulnerabilities_list):
    """Return a sample search response with pagination."""
    return {
        "content": sample_vulnerabilities_list,
        "totalElements": 100,
        "totalPages": 10,
        "page": 0,
        "size": 10,
    }


@pytest.fixture
def sample_advisory():
    """Return a sample advisory response."""
    return {
        "id": "cisco-sa-ata19x-multi-RDTEqRsy",
        "description": "Test advisory description",
        "summary": "Test summary",
        "datePublished": "2024-01-01T00:00:00Z",
        "dateUpdated": "2024-12-13T00:00:00Z",
        "baseScore": 7.5,
        "references": "https://example.com/adv1",
        "aliases": "CVE-2024-12347",
        "source": {"id": 1, "name": "Cisco"},
        "advisoryProduct": [],
        "enisaIdAdvisories": [],
        "vulnerabilityAdvisory": [],
    }


@pytest.fixture
def mock_api_manager(mocker):
    """Return a mocked API manager."""
    manager = MagicMock(spec=EUVDAPIManager)
    return manager


@pytest.fixture
def api_manager():
    """Return a real API manager instance for unit tests."""
    return EUVDAPIManager(timeout=10, max_retries=1)


@pytest.fixture
def mock_requests_get(mocker):
    """Return a mocked requests.get function."""
    return mocker.patch("euvd_mcp.controllers.euvd_api.requests.Session.get")
