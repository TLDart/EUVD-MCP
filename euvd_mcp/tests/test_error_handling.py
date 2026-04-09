"""
Tests for the _handle_tool_errors decorator and _http_error_detail helper.
"""

import httpx
import pytest
from pydantic import ValidationError

from euvd_mcp.main import (
    _format_validation_error,
    _handle_tool_errors,
    _http_error_detail,
)
from euvd_mcp.models import GetVulnerabilityByIdInput


class TestHttpErrorDetail:
    def test_404(self):
        assert "not found" in _http_error_detail(404).lower()

    def test_429(self):
        assert "rate limit" in _http_error_detail(429).lower()

    def test_500(self):
        assert "internal server error" in _http_error_detail(500).lower()

    def test_unknown_status(self):
        detail = _http_error_detail(418)
        assert "418" in detail


class TestFormatValidationError:
    def test_single_field_error(self):
        with pytest.raises(ValidationError) as exc_info:
            GetVulnerabilityByIdInput(enisa_id="bad-id")
        result = _format_validation_error(exc_info.value)
        assert "enisa_id" in result

    def test_returns_string(self):
        with pytest.raises(ValidationError) as exc_info:
            GetVulnerabilityByIdInput(enisa_id="")
        assert isinstance(_format_validation_error(exc_info.value), str)


class TestHandleToolErrors:
    async def test_passes_through_successful_result(self):
        @_handle_tool_errors
        async def tool() -> dict:
            return {"data": "ok"}

        result = await tool()
        assert result == {"data": "ok"}

    async def test_catches_validation_error(self):
        @_handle_tool_errors
        async def tool() -> dict:
            raise ValidationError.from_exception_data(
                title="Test",
                input_type="python",
                line_errors=[
                    {
                        "type": "missing",
                        "loc": ("field",),
                        "msg": "Field required",
                        "input": {},
                        "url": "https://errors.pydantic.dev/2/v/missing",
                    }
                ],
            )

        result = await tool()
        assert result["error"] == "validation_error"
        assert "detail" in result

    async def test_catches_http_status_error_4xx(self):
        @_handle_tool_errors
        async def tool() -> dict:
            request = httpx.Request("GET", "https://example.com/api")
            response = httpx.Response(404, request=request)
            raise httpx.HTTPStatusError("Not found", request=request, response=response)

        result = await tool()
        assert result["error"] == "http_error"
        assert result["status_code"] == 404
        assert "not found" in result["detail"].lower()

    async def test_catches_http_status_error_5xx(self):
        @_handle_tool_errors
        async def tool() -> dict:
            request = httpx.Request("GET", "https://example.com/api")
            response = httpx.Response(503, request=request)
            raise httpx.HTTPStatusError(
                "Unavailable", request=request, response=response
            )

        result = await tool()
        assert result["error"] == "http_error"
        assert result["status_code"] == 503

    async def test_catches_transport_error(self):
        @_handle_tool_errors
        async def tool() -> dict:
            raise httpx.ConnectError("Connection refused")

        result = await tool()
        assert result["error"] == "connection_error"
        assert "EUVD API" in result["detail"]

    async def test_catches_unexpected_exception(self):
        @_handle_tool_errors
        async def tool() -> dict:
            raise RuntimeError("something went wrong")

        result = await tool()
        assert result["error"] == "unexpected_error"
        assert "server logs" in result["detail"]

    async def test_preserves_function_name(self):
        @_handle_tool_errors
        async def my_tool() -> dict:
            return {}

        assert my_tool.__name__ == "my_tool"

    async def test_preserves_docstring(self):
        @_handle_tool_errors
        async def my_tool() -> dict:
            """My tool docstring."""
            return {}

        assert my_tool.__doc__ == "My tool docstring."
