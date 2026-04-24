"""Tests for the Duplicacy config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.duplicacy.api import DuplicacyApiClient, DuplicacyConnectionError
from custom_components.duplicacy.config_flow import DuplicacyConfigFlow
from custom_components.duplicacy.const import CONF_URL, DEFAULT_URL, DOMAIN


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def test_domain_constant() -> None:
    """Test the domain is correctly defined."""
    assert DOMAIN == "duplicacy"


def test_default_url() -> None:
    """Test the default URL."""
    assert DEFAULT_URL == "http://localhost:9750"


def test_conf_url_constant() -> None:
    """Test the CONF_URL constant."""
    assert CONF_URL == "url"


# ---------------------------------------------------------------------------
# Config flow version
# ---------------------------------------------------------------------------

def test_config_flow_version() -> None:
    """Test config flow version is 1."""
    assert DuplicacyConfigFlow.VERSION == 1


# ---------------------------------------------------------------------------
# DuplicacyConfigFlow.async_step_user
# ---------------------------------------------------------------------------

class TestAsyncStepUser:
    """Tests for the user config flow step."""

    @pytest.mark.asyncio
    async def test_shows_form_when_no_input(self) -> None:
        """Test that form is shown when user_input is None."""
        flow = DuplicacyConfigFlow()

        result = await flow.async_step_user(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    @pytest.mark.asyncio
    async def test_creates_entry_on_successful_health_check(self) -> None:
        """Test entry is created when health check succeeds."""
        flow = DuplicacyConfigFlow()

        mock_client = MagicMock()
        mock_client.check_health = AsyncMock(return_value=True)

        with patch("custom_components.duplicacy.config_flow.aiohttp.ClientSession") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            with patch(
                "custom_components.duplicacy.config_flow.DuplicacyApiClient",
                return_value=mock_client,
            ):
                result = await flow.async_step_user(
                    user_input={CONF_URL: "http://example.com:9750/"}
                )

        assert result["type"] == "create_entry"
        assert result["data"][CONF_URL] == "http://example.com:9750"
        assert "Duplicacy" in result["title"]

    @pytest.mark.asyncio
    async def test_shows_error_on_connection_failure(self) -> None:
        """Test form is re-shown with error when connection fails."""
        flow = DuplicacyConfigFlow()

        mock_client = MagicMock()
        mock_client.check_health = AsyncMock(
            side_effect=DuplicacyConnectionError("unreachable")
        )

        with patch("custom_components.duplicacy.config_flow.aiohttp.ClientSession") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            with patch(
                "custom_components.duplicacy.config_flow.DuplicacyApiClient",
                return_value=mock_client,
            ):
                result = await flow.async_step_user(
                    user_input={CONF_URL: "http://bad:9750"}
                )

        assert result["type"] == "form"
        assert result["errors"]["base"] == "cannot_connect"

    @pytest.mark.asyncio
    async def test_shows_error_on_unexpected_exception(self) -> None:
        """Test form is re-shown with 'unknown' error on unexpected exception."""
        flow = DuplicacyConfigFlow()

        mock_client = MagicMock()
        mock_client.check_health = AsyncMock(side_effect=RuntimeError("boom"))

        with patch("custom_components.duplicacy.config_flow.aiohttp.ClientSession") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            with patch(
                "custom_components.duplicacy.config_flow.DuplicacyApiClient",
                return_value=mock_client,
            ):
                result = await flow.async_step_user(
                    user_input={CONF_URL: "http://bad:9750"}
                )

        assert result["type"] == "form"
        assert result["errors"]["base"] == "unknown"

    @pytest.mark.asyncio
    async def test_strips_trailing_slash_from_url(self) -> None:
        """Test URL trailing slash is stripped before unique_id and entry."""
        flow = DuplicacyConfigFlow()

        # Track the unique_id that gets set
        captured_uid = []
        original_set_uid = flow.async_set_unique_id
        async def capture_uid(uid):
            captured_uid.append(uid)
            return await original_set_uid(uid)
        flow.async_set_unique_id = capture_uid

        mock_client = MagicMock()
        mock_client.check_health = AsyncMock(return_value=True)

        with patch("custom_components.duplicacy.config_flow.aiohttp.ClientSession") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            with patch(
                "custom_components.duplicacy.config_flow.DuplicacyApiClient",
                return_value=mock_client,
            ):
                result = await flow.async_step_user(
                    user_input={CONF_URL: "http://host:9750/"}
                )

        # unique_id should be the stripped URL
        assert captured_uid[0] == "http://host:9750"
        # Entry data should also have stripped URL
        assert result["data"][CONF_URL] == "http://host:9750"

    @pytest.mark.asyncio
    async def test_entry_title_contains_url(self) -> None:
        """Test the entry title includes the URL."""
        flow = DuplicacyConfigFlow()

        mock_client = MagicMock()
        mock_client.check_health = AsyncMock(return_value=True)

        with patch("custom_components.duplicacy.config_flow.aiohttp.ClientSession") as mock_session_cls:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_session

            with patch(
                "custom_components.duplicacy.config_flow.DuplicacyApiClient",
                return_value=mock_client,
            ):
                result = await flow.async_step_user(
                    user_input={CONF_URL: "http://myhost:9750"}
                )

        assert result["title"] == "Duplicacy (http://myhost:9750)"


# ---------------------------------------------------------------------------
# URL handling (via DuplicacyApiClient)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_url_trailing_slash_stripped_in_client() -> None:
    """Test that trailing slashes are stripped in the API client."""
    async with aiohttp.ClientSession() as session:
        client = DuplicacyApiClient("http://duplicacy:9750/", session)
        assert client._url == "http://duplicacy:9750"


@pytest.mark.asyncio
async def test_connection_error_detection() -> None:
    """Test that unreachable servers are detected."""
    async with aiohttp.ClientSession() as session:
        client = DuplicacyApiClient("http://127.0.0.1:1", session)
        with pytest.raises(DuplicacyConnectionError):
            await client.check_health()
