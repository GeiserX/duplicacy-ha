"""Tests for the Duplicacy config flow logic."""

from __future__ import annotations

import pytest

from custom_components.duplicacy.api import DuplicacyConnectionError
from custom_components.duplicacy.const import CONF_URL, DEFAULT_URL, DOMAIN


def test_domain_constant() -> None:
    """Test the domain is correctly defined."""
    assert DOMAIN == "duplicacy"


def test_default_url() -> None:
    """Test the default URL."""
    assert DEFAULT_URL == "http://localhost:9750"


@pytest.mark.asyncio
async def test_connection_error_detection() -> None:
    """Test that unreachable servers are detected."""
    from custom_components.duplicacy.api import DuplicacyApiClient
    import aiohttp

    async with aiohttp.ClientSession() as session:
        client = DuplicacyApiClient("http://127.0.0.1:1", session)
        with pytest.raises(DuplicacyConnectionError):
            await client.check_health()


@pytest.mark.asyncio
async def test_url_trailing_slash_stripped() -> None:
    """Test that trailing slashes are stripped."""
    from custom_components.duplicacy.api import DuplicacyApiClient
    import aiohttp

    async with aiohttp.ClientSession() as session:
        client = DuplicacyApiClient("http://duplicacy:9750/", session)
        assert client._url == "http://duplicacy:9750"
