"""Tests for the Duplicacy coordinator data logic."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.duplicacy.api import DuplicacyApiError
from custom_components.duplicacy.const import DEFAULT_SCAN_INTERVAL

from .conftest import MOCK_METRICS_PARSED


def test_default_scan_interval() -> None:
    """Verify default scan interval is 30 seconds."""
    assert DEFAULT_SCAN_INTERVAL == 30


@pytest.mark.asyncio
async def test_fetch_metrics_success() -> None:
    """Test successful metric fetch."""
    client = MagicMock()
    client.get_metrics = AsyncMock(return_value=MOCK_METRICS_PARSED)

    data = await client.get_metrics()

    assert ("documents", "b2") in data
    assert data[("documents", "b2")]["duplicacy_backup_last_duration_seconds"] == 120.5


@pytest.mark.asyncio
async def test_fetch_metrics_error() -> None:
    """Test API error propagation."""
    client = MagicMock()
    client.get_metrics = AsyncMock(side_effect=DuplicacyApiError("fail"))

    with pytest.raises(DuplicacyApiError):
        await client.get_metrics()
