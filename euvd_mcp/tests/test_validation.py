"""
Unit tests for Pydantic input models in models/input_models.py.
"""

import pytest
from pydantic import ValidationError

from euvd_mcp.models import (
    GetAdvisoryByIdInput,
    GetVulnerabilityByIdInput,
    SearchVulnerabilitiesInput,
)


class TestSearchVulnerabilitiesInputScores:
    """Tests for CVSS and EPSS score validation."""

    def test_valid_score_boundaries(self):
        m = SearchVulnerabilitiesInput(from_score=0.0, to_score=10.0)
        assert m.from_score == 0.0
        assert m.to_score == 10.0

    def test_valid_epss_boundaries(self):
        m = SearchVulnerabilitiesInput(from_epss=0.0, to_epss=100.0)
        assert m.from_epss == 0.0
        assert m.to_epss == 100.0

    def test_score_below_zero(self):
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            SearchVulnerabilitiesInput(from_score=-0.1)

    def test_score_above_ten(self):
        with pytest.raises(ValidationError, match="less than or equal to 10"):
            SearchVulnerabilitiesInput(to_score=10.1)

    def test_epss_below_zero(self):
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            SearchVulnerabilitiesInput(from_epss=-1.0)

    def test_epss_above_hundred(self):
        with pytest.raises(ValidationError, match="less than or equal to 100"):
            SearchVulnerabilitiesInput(to_epss=100.1)


class TestSearchVulnerabilitiesInputDates:
    """Tests for date field validation."""

    def test_valid_date(self):
        m = SearchVulnerabilitiesInput(from_date="2024-01-15", to_date="2024-12-31")
        assert m.from_date == "2024-01-15"
        assert m.to_date == "2024-12-31"

    def test_valid_updated_dates(self):
        m = SearchVulnerabilitiesInput(
            from_updated_date="2024-06-01", to_updated_date="2024-06-30"
        )
        assert m.from_updated_date == "2024-06-01"

    def test_wrong_format_slashes(self):
        with pytest.raises(ValidationError, match="YYYY-MM-DD"):
            SearchVulnerabilitiesInput(from_date="2024/01/15")

    def test_wrong_format_no_separators(self):
        with pytest.raises(ValidationError, match="YYYY-MM-DD"):
            SearchVulnerabilitiesInput(to_date="20240115")

    def test_invalid_calendar_date(self):
        with pytest.raises(ValidationError, match="not a valid calendar date"):
            SearchVulnerabilitiesInput(from_date="2024-02-30")

    def test_invalid_month(self):
        with pytest.raises(ValidationError, match="not a valid calendar date"):
            SearchVulnerabilitiesInput(from_date="2024-13-01")

    def test_none_dates_allowed(self):
        m = SearchVulnerabilitiesInput(from_date=None, to_date=None)
        assert m.from_date is None


class TestSearchVulnerabilitiesInputPagination:
    """Tests for pagination field validation."""

    def test_valid_page_and_size(self):
        m = SearchVulnerabilitiesInput(page=0, size=50)
        assert m.page == 0
        assert m.size == 50

    def test_size_boundary_min(self):
        m = SearchVulnerabilitiesInput(size=1)
        assert m.size == 1

    def test_size_boundary_max(self):
        m = SearchVulnerabilitiesInput(size=100)
        assert m.size == 100

    def test_size_zero(self):
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            SearchVulnerabilitiesInput(size=0)

    def test_size_above_max(self):
        with pytest.raises(ValidationError, match="less than or equal to 100"):
            SearchVulnerabilitiesInput(size=101)

    def test_negative_page(self):
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            SearchVulnerabilitiesInput(page=-1)


class TestSearchVulnerabilitiesInputAllNone:
    """Test that all fields are optional."""

    def test_empty_model_is_valid(self):
        m = SearchVulnerabilitiesInput()
        assert m.model_dump(exclude_none=True) == {}

    def test_model_dump_excludes_none(self):
        m = SearchVulnerabilitiesInput(from_score=7.5, vendor="Microsoft")
        dumped = m.model_dump(exclude_none=True)
        assert "from_score" in dumped
        assert "vendor" in dumped
        assert "to_score" not in dumped


class TestGetVulnerabilityByIdInput:
    """Tests for GetVulnerabilityByIdInput."""

    def test_valid_short_id(self):
        m = GetVulnerabilityByIdInput(enisa_id="EUVD-2025-4893")
        assert m.enisa_id == "EUVD-2025-4893"

    def test_valid_long_id(self):
        m = GetVulnerabilityByIdInput(enisa_id="EUVD-2024-45012")
        assert m.enisa_id == "EUVD-2024-45012"

    def test_lowercase_prefix_rejected(self):
        with pytest.raises(ValidationError, match="EUVD-YYYY-N format"):
            GetVulnerabilityByIdInput(enisa_id="euvd-2024-45012")

    def test_cve_format_rejected(self):
        with pytest.raises(ValidationError, match="EUVD-YYYY-N format"):
            GetVulnerabilityByIdInput(enisa_id="CVE-2024-45012")

    def test_missing_year_rejected(self):
        with pytest.raises(ValidationError, match="EUVD-YYYY-N format"):
            GetVulnerabilityByIdInput(enisa_id="EUVD-45012")

    def test_empty_string_rejected(self):
        with pytest.raises(ValidationError, match="EUVD-YYYY-N format"):
            GetVulnerabilityByIdInput(enisa_id="")


class TestGetAdvisoryByIdInput:
    """Tests for GetAdvisoryByIdInput."""

    def test_valid_advisory_id(self):
        m = GetAdvisoryByIdInput(advisory_id="cisco-sa-ata19x-multi-RDTEqRsy")
        assert m.advisory_id == "cisco-sa-ata19x-multi-RDTEqRsy"

    def test_another_valid_id(self):
        m = GetAdvisoryByIdInput(advisory_id="oxas-adv-2024-0002")
        assert m.advisory_id == "oxas-adv-2024-0002"

    def test_missing_advisory_id(self):
        with pytest.raises(ValidationError):
            GetAdvisoryByIdInput()  # type: ignore[call-arg]
