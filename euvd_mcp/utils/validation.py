"""Validation Lib."""

import re
from datetime import datetime

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ENISA_ID_RE = re.compile(r"^EUVD-\d{4}-\d+$")


def _validate_score(value: float, name: str) -> None:
    if not 0.0 <= value <= 10.0:
        raise ValueError(f"{name} must be between 0.0 and 10.0, got {value}")


def _validate_epss(value: float, name: str) -> None:
    if not 0.0 <= value <= 100.0:
        raise ValueError(f"{name} must be between 0.0 and 100.0, got {value}")


def _validate_date(value: str, name: str) -> None:
    if not _DATE_RE.match(value):
        raise ValueError(f"{name} must be in YYYY-MM-DD format, got {value!r}")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{name} is not a valid calendar date: {value!r}")


def _validate_enisa_id(enisa_id: str) -> None:
    if not _ENISA_ID_RE.match(enisa_id):
        raise ValueError(
            f"enisa_id must match EUVD-YYYY-N format (e.g. 'EUVD-2024-45012'), got {enisa_id!r}"
        )
