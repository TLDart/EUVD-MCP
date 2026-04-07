"""
Pydantic input models for EUVD MCP tool parameters.

Each model describes the accepted input for a specific tool and enforces
all validation constraints through Pydantic field definitions and validators.
"""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ENISA_ID_RE = re.compile(r"^EUVD-\d{4}-\d+$")


def _validate_date_string(value: str, field_name: str) -> str:
    if not _DATE_RE.match(value):
        raise ValueError(f"{field_name} must be in YYYY-MM-DD format, got {value!r}")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{field_name} is not a valid calendar date: {value!r}")
    return value


class SearchVulnerabilitiesInput(BaseModel):
    """Input model for the search_vulnerabilities tool."""

    from_score: float | None = Field(
        None, ge=0.0, le=10.0, description="Minimum CVSS score (0.0-10.0)"
    )
    to_score: float | None = Field(
        None, ge=0.0, le=10.0, description="Maximum CVSS score (0.0-10.0)"
    )
    from_epss: float | None = Field(
        None, ge=0.0, le=100.0, description="Minimum EPSS score (0.0-100.0)"
    )
    to_epss: float | None = Field(
        None, ge=0.0, le=100.0, description="Maximum EPSS score (0.0-100.0)"
    )
    from_date: str | None = Field(
        None, description="Start publication date in YYYY-MM-DD format"
    )
    to_date: str | None = Field(
        None, description="End publication date in YYYY-MM-DD format"
    )
    from_updated_date: str | None = Field(
        None, description="Start updated date in YYYY-MM-DD format"
    )
    to_updated_date: str | None = Field(
        None, description="End updated date in YYYY-MM-DD format"
    )
    product: str | None = Field(
        None, description="Product name filter (e.g., 'Windows')"
    )
    vendor: str | None = Field(
        None, description="Vendor name filter (e.g., 'Microsoft')"
    )
    assigner: str | None = Field(None, description="Assigner filter (e.g., 'mitre')")
    exploited: bool | None = Field(None, description="Filter by exploited status")
    text: str | None = Field(None, description="Keyword search")
    page: int | None = Field(None, ge=0, description="Page number (starts at 0)")
    size: int | None = Field(
        None, ge=1, le=100, description="Page size (1-100, default 10)"
    )

    @field_validator(
        "from_date", "to_date", "from_updated_date", "to_updated_date", mode="before"
    )
    @classmethod
    def validate_date(cls, v: str | None, info: object) -> str | None:
        """Validate date string fields are in YYYY-MM-DD format."""
        if v is None:
            return v
        return _validate_date_string(v, str(getattr(info, "field_name", "date")))


class GetVulnerabilityByIdInput(BaseModel):
    """Input model for the get_vulnerability_by_id tool."""

    enisa_id: str = Field(
        description="EUVD identifier (e.g., 'EUVD-2025-4893' or 'EUVD-2024-45012')"
    )

    @field_validator("enisa_id")
    @classmethod
    def validate_enisa_id(cls, v: str) -> str:
        """Validate ENISA ID matches the EUVD-YYYY-N pattern."""
        if not _ENISA_ID_RE.match(v):
            raise ValueError(
                f"enisa_id must match EUVD-YYYY-N format (e.g. 'EUVD-2024-45012'), got {v!r}"
            )
        return v


class GetAdvisoryByIdInput(BaseModel):
    """Input model for the get_advisory_by_id tool."""

    advisory_id: str = Field(
        description="Advisory identifier (e.g., 'oxas-adv-2024-0002' or 'cisco-sa-ata19x-multi-RDTEqRsy')"
    )
