"""Tests for the Duplicacy API client."""

from __future__ import annotations

import pytest
from aiohttp import ClientSession
from aiohttp.test_utils import TestServer
from aiohttp.web import Application, Request, Response

from custom_components.duplicacy.api import (
    DuplicacyApiClient,
    DuplicacyApiError,
    DuplicacyConnectionError,
    _parse_metrics,
)

from .conftest import MOCK_METRICS_TEXT


def test_parse_metrics_basic() -> None:
    """Test parsing Prometheus text format."""
    result = _parse_metrics(MOCK_METRICS_TEXT)
    key = ("documents", "b2")
    assert key in result
    assert result[key]["machine"] == "server1"
    assert result[key]["duplicacy_backup_last_success_timestamp_seconds"] == 1704067200.0
    assert result[key]["duplicacy_backup_last_duration_seconds"] == 120.5
    assert result[key]["duplicacy_backup_running"] == 0.0


def test_parse_metrics_empty() -> None:
    """Test parsing empty text."""
    result = _parse_metrics("")
    assert result == {}


def test_parse_metrics_comments_only() -> None:
    """Test parsing only comments."""
    result = _parse_metrics("# HELP foo\n# TYPE foo gauge\n")
    assert result == {}


def test_parse_metrics_invalid_value() -> None:
    """Test that non-numeric values are skipped."""
    text = 'metric_name{snapshot_id="a",storage_target="b"} NaN_bad\n'
    result = _parse_metrics(text)
    assert result == {}


def test_parse_metrics_multiple_jobs() -> None:
    """Test parsing metrics for multiple backup jobs."""
    text = (
        'duplicacy_backup_running{snapshot_id="docs",storage_target="b2",machine="s1"} 0\n'
        'duplicacy_backup_running{snapshot_id="photos",storage_target="s3",machine="s2"} 1\n'
    )
    result = _parse_metrics(text)
    assert ("docs", "b2") in result
    assert ("photos", "s3") in result
    assert result[("docs", "b2")]["duplicacy_backup_running"] == 0.0
    assert result[("photos", "s3")]["duplicacy_backup_running"] == 1.0


def test_parse_metrics_no_labels() -> None:
    """Test parsing a metric without labels."""
    text = "some_metric 42\n"
    result = _parse_metrics(text)
    key = ("", "")
    assert key in result
    assert result[key]["some_metric"] == 42.0


@pytest.mark.asyncio
async def test_check_health_success() -> None:
    """Test successful health check."""
    app = Application()

    async def handle(request: Request) -> Response:
        return Response(status=200, text="ok")

    app.router.add_get("/health", handle)

    async with TestServer(app) as server:
        async with ClientSession() as session:
            client = DuplicacyApiClient(str(server.make_url("")), session)
            result = await client.check_health()
            assert result is True


@pytest.mark.asyncio
async def test_check_health_connection_error() -> None:
    """Test health check on unreachable server."""
    async with ClientSession() as session:
        client = DuplicacyApiClient("http://127.0.0.1:1", session)
        with pytest.raises(DuplicacyConnectionError):
            await client.check_health()


@pytest.mark.asyncio
async def test_get_metrics_success() -> None:
    """Test fetching and parsing metrics."""
    app = Application()

    async def handle(request: Request) -> Response:
        return Response(status=200, text=MOCK_METRICS_TEXT)

    app.router.add_get("/metrics", handle)

    async with TestServer(app) as server:
        async with ClientSession() as session:
            client = DuplicacyApiClient(str(server.make_url("")), session)
            result = await client.get_metrics()
            assert ("documents", "b2") in result


@pytest.mark.asyncio
async def test_get_metrics_http_error() -> None:
    """Test metrics endpoint returning error status."""
    app = Application()

    async def handle(request: Request) -> Response:
        return Response(status=500)

    app.router.add_get("/metrics", handle)

    async with TestServer(app) as server:
        async with ClientSession() as session:
            client = DuplicacyApiClient(str(server.make_url("")), session)
            with pytest.raises(DuplicacyApiError):
                await client.get_metrics()


@pytest.mark.asyncio
async def test_get_metrics_connection_error() -> None:
    """Test metrics on unreachable server."""
    async with ClientSession() as session:
        client = DuplicacyApiClient("http://127.0.0.1:1", session)
        with pytest.raises(DuplicacyConnectionError):
            await client.get_metrics()
