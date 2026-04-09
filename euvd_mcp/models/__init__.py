"""Pydantic models for EUVD API responses and tool inputs."""

from .input_models import (
    GetAdvisoryByIdInput,
    GetVulnerabilityByIdInput,
    SearchVulnerabilitiesInput,
)
from .vulnerability import (
    Advisory,
    ExploitedVulnerabilities,
    SearchResponse,
    Vulnerability,
    VulnerabilityListResponse,
)

__all__ = [
    # Response models
    "Vulnerability",
    "VulnerabilityListResponse",
    "ExploitedVulnerabilities",
    "SearchResponse",
    "Advisory",
    # Input models
    "SearchVulnerabilitiesInput",
    "GetVulnerabilityByIdInput",
    "GetAdvisoryByIdInput",
]
