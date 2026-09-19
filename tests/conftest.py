"""
Global PyTest configuration and fixtures for the API test framework.

Designed to run identically locally and in GitHub Actions:
- Config comes from environment variables (via config.settings) with .env fallback.
- Every request/response is attached to the Allure report for CI debugging.
- Explicit timeouts on every request prevent CI hangs.
"""

import json
import os
from pathlib import Path
from typing import Generator

import allure
import jsonschema
import pytest
import requests
from requests import Response, Session

from config.settings import settings


# ============================================================
# CLI Options
# ============================================================
def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--base-url",
        action="store",
        default=settings.base_url,
        help="Base URL for the API under test",
    )
    parser.addoption(
        "--api-timeout",
        action="store",
        default=settings.api_timeout,
        type=int,
        help="Request timeout in seconds (critical for CI to prevent hangs)",
    )


# ============================================================
# Allure Environment Info (shown at the top of the report)
# ============================================================
@pytest.fixture(scope="session", autouse=True)
def allure_environment(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Write environment info to allure-results so CI reports show context."""
    results_dir = "allure-results"
    os.makedirs(results_dir, exist_ok=True)

    env_info = {
        "Base.URL": settings.base_url,
        "Environment": settings.environment,
        "Timeout.Seconds": settings.api_timeout,
        "Python.Version": os.sys.version.split()[0],
        "CI": os.getenv("GITHUB_ACTIONS", "false"),
        "Runner.OS": os.getenv("RUNNER_OS", "local"),
        "Git.Branch": os.getenv("GITHUB_REF_NAME", "local"),
        "Git.SHA": os.getenv("GITHUB_SHA", "local")[:7],
    }

    with open(os.path.join(results_dir, "environment.properties"), "w") as f:
        for key, value in env_info.items():
            f.write(f"{key}={value}\n")

    yield


# ============================================================
# API Session Fixtures
# ============================================================
@pytest.fixture(scope="session")
def base_url(request: pytest.FixtureRequest) -> str:
    """Return the base URL for the API under test."""
    return request.config.getoption("--base-url").rstrip("/")


@pytest.fixture(scope="session")
def api_timeout(request: pytest.FixtureRequest) -> int:
    """Return the request timeout in seconds."""
    return request.config.getoption("--api-timeout")


@pytest.fixture(scope="session")
def api_session(base_url: str, api_timeout: int) -> Generator[Session, None, None]:
    """
    Session-scoped requests.Session with:
    - Connection pooling (faster across tests)
    - Default timeout (prevents CI hangs)
    - Allure attachments on every request/response (for CI debugging)
    - Standard JSON headers
    """
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "python-api-test-framework/1.0",
        }
    )

    if settings.api_token:
        session.headers.update({"Authorization": f"Bearer {settings.api_token}"})

    # Wrap requests so every call is logged to Allure and gets a default timeout
    original_request = session.request

    def logged_request(method: str, url: str, **kwargs) -> Response:
        # Ensure timeout is always set (falls back to configured default)
        kwargs.setdefault("timeout", api_timeout)
        # Allow relative URLs and prepend base_url
        if url.startswith("/"):
            url = base_url + url

        # Attach the request to Allure
        with allure.step(f"{method.upper()} {url}"):
            allure.attach(
                _format_request(method, url, kwargs),
                name=f"Request: {method.upper()} {url}",
                attachment_type=allure.attachment_type.TEXT,
            )

            response = original_request(method, url, **kwargs)

            allure.attach(
                _format_response(response),
                name=f"Response: {response.status_code}",
                attachment_type=allure.attachment_type.TEXT,
            )

            return response

    session.request = logged_request  # type: ignore[method-assign]

    yield session

    session.close()


# ============================================================
# JSON Schema Validation Fixture
# ============================================================
@pytest.fixture(scope="session")
def validate_schema() -> callable:
    """
    Returns a function that validates a payload against a JSON Schema file.

    Usage:
        validate_schema(response.json(), "post_schema.json")
    """
    schemas_dir = Path(__file__).parent.parent / "schemas"

    def _validate(payload: object, schema_filename: str) -> None:
        schema_path = schemas_dir / schema_filename
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)

        try:
            jsonschema.validate(instance=payload, schema=schema)
        except jsonschema.ValidationError as e:
            # Attach the full error to Allure for CI debugging
            allure.attach(
                str(e),
                name=f"Schema Validation Error: {schema_filename}",
                attachment_type=allure.attachment_type.TEXT,
            )
            raise AssertionError(
                f"Schema validation failed for '{schema_filename}': {e.message}"
            ) from e

    return _validate


# ============================================================
# Helpers
# ============================================================
def _format_request(method: str, url: str, kwargs: dict) -> str:
    """Format an HTTP request for Allure logging."""
    lines = [f"{method.upper()} {url}"]
    if headers := kwargs.get("headers"):
        lines.append("\n--- Headers ---")
        lines.extend(f"{k}: {v}" for k, v in headers.items())
    if params := kwargs.get("params"):
        lines.append(f"\n--- Query Params ---\n{params}")
    if json_body := kwargs.get("json"):
        lines.append(f"\n--- JSON Body ---\n{json_body}")
    if data := kwargs.get("data"):
        lines.append(f"\n--- Form Data ---\n{data}")
    return "\n".join(lines)


def _format_response(response: Response) -> str:
    """Format an HTTP response for Allure logging."""
    lines = [f"Status: {response.status_code} {response.reason}"]
    lines.append(f"Elapsed: {response.elapsed.total_seconds():.3f}s")
    lines.append("\n--- Headers ---")
    lines.extend(f"{k}: {v}" for k, v in response.headers.items())
    lines.append("\n--- Body ---")
    try:
        lines.append(response.text[:5000])  # truncate huge bodies
    except Exception:
        lines.append("<unable to decode body>")
    return "\n".join(lines)