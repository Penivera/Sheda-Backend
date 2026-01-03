"""
Tests for the WebSocket service at /ws/{user_id}
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket
from app.routers.websocket import (
    WebSocketConnectionManager,
    authenticate_websocket_user,
    ws_manager,
)


class TestWebSocketConnectionManager:
    """Tests for the WebSocketConnectionManager class."""

    def setup_method(self):
        """Reset the connection manager before each test."""
        self.manager = WebSocketConnectionManager()

    @pytest.mark.asyncio
    async def test_connect_stores_connection(self):
        """Test that connect properly stores the WebSocket connection."""
        mock_websocket = AsyncMock(spec=WebSocket)
        user_id = 1

        result = await self.manager.connect(mock_websocket, user_id)

        assert result is True
        assert user_id in self.manager.active_connections
        assert self.manager.active_connections[user_id] == mock_websocket
        mock_websocket.accept.assert_called_once()

    def test_disconnect_removes_connection(self):
        """Test that disconnect removes the user's connection."""
        mock_websocket = AsyncMock(spec=WebSocket)
        user_id = 1
        self.manager.active_connections[user_id] = mock_websocket

        self.manager.disconnect(user_id)

        assert user_id not in self.manager.active_connections

    def test_disconnect_nonexistent_user_no_error(self):
        """Test that disconnecting a non-existent user doesn't raise an error."""
        # Should not raise an exception
        self.manager.disconnect(999)

    def test_is_connected_returns_true_when_connected(self):
        """Test is_connected returns True for connected users."""
        mock_websocket = AsyncMock(spec=WebSocket)
        user_id = 1
        self.manager.active_connections[user_id] = mock_websocket

        assert self.manager.is_connected(user_id) is True

    def test_is_connected_returns_false_when_not_connected(self):
        """Test is_connected returns False for disconnected users."""
        assert self.manager.is_connected(999) is False

    @pytest.mark.asyncio
    async def test_send_personal_message_to_connected_user(self):
        """Test sending a message to a connected user."""
        mock_websocket = AsyncMock(spec=WebSocket)
        user_id = 1
        self.manager.active_connections[user_id] = mock_websocket
        message = {"type": "test", "content": "Hello"}

        result = await self.manager.send_personal_message(message, user_id)

        assert result is True
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_message_to_disconnected_user(self):
        """Test sending a message to a disconnected user returns False."""
        message = {"type": "test", "content": "Hello"}

        result = await self.manager.send_personal_message(message, 999)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_personal_message_cleans_up_broken_connection(self):
        """Test that broken connections are cleaned up when sending fails."""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.send_json.side_effect = Exception("Connection broken")
        user_id = 1
        self.manager.active_connections[user_id] = mock_websocket

        result = await self.manager.send_personal_message({"test": "data"}, user_id)

        assert result is False
        assert user_id not in self.manager.active_connections

    def test_get_connected_users(self):
        """Test getting list of connected user IDs."""
        self.manager.active_connections[1] = AsyncMock()
        self.manager.active_connections[2] = AsyncMock()
        self.manager.active_connections[3] = AsyncMock()

        connected_users = self.manager.get_connected_users()

        assert sorted(connected_users) == [1, 2, 3]


class TestAuthenticateWebSocketUser:
    """Tests for WebSocket authentication."""

    @pytest.mark.asyncio
    async def test_auth_fails_without_token(self):
        """Test that authentication fails when no token is provided."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.headers = {}
        mock_db = AsyncMock()

        result = await authenticate_websocket_user(
            mock_websocket, user_id=1, db=mock_db, token=None
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_auth_extracts_token_from_bearer_protocol(self):
        """Test token extraction from Sec-WebSocket-Protocol header with Bearer prefix."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.headers = {
            "sec-websocket-protocol": "Bearer.test_token_value"
        }
        mock_db = AsyncMock()

        with patch("app.routers.websocket.redis") as mock_redis:
            mock_redis.get.return_value = None  # Token not blacklisted

            with patch("app.routers.websocket.jwt.decode") as mock_jwt:
                mock_jwt.return_value = {"sub": "1", "scopes": ["client"]}

                with patch("app.routers.websocket.get_user") as mock_get_user:
                    mock_user = MagicMock()
                    mock_user.id = 1
                    mock_user.is_active = True
                    mock_user.verified = True
                    mock_user.email = "test@example.com"
                    mock_get_user.return_value = mock_user

                    result = await authenticate_websocket_user(
                        mock_websocket, user_id=1, db=mock_db, token=None
                    )

                    assert result is not None
                    assert result.id == 1

    @pytest.mark.asyncio
    async def test_auth_fails_for_blacklisted_token(self):
        """Test that authentication fails for blacklisted tokens."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.headers = {}
        mock_db = AsyncMock()

        with patch("app.routers.websocket.redis") as mock_redis:
            mock_redis.get.return_value = b"blacklisted"  # Token is blacklisted

            result = await authenticate_websocket_user(
                mock_websocket, user_id=1, db=mock_db, token="blacklisted_token"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_auth_fails_for_user_id_mismatch(self):
        """Test that authentication fails when path user_id doesn't match token user."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.headers = {}
        mock_db = AsyncMock()

        with patch("app.routers.websocket.redis") as mock_redis:
            mock_redis.get.return_value = None

            with patch("app.routers.websocket.jwt.decode") as mock_jwt:
                mock_jwt.return_value = {"sub": "1", "scopes": ["client"]}

                with patch("app.routers.websocket.get_user") as mock_get_user:
                    mock_user = MagicMock()
                    mock_user.id = 1  # Token user ID
                    mock_user.is_active = True
                    mock_user.verified = True
                    mock_get_user.return_value = mock_user

                    # Path user_id is 2, but token user is 1
                    result = await authenticate_websocket_user(
                        mock_websocket, user_id=2, db=mock_db, token="valid_token"
                    )

                    assert result is None

    @pytest.mark.asyncio
    async def test_auth_fails_for_inactive_user(self):
        """Test that authentication fails for inactive users."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.headers = {}
        mock_db = AsyncMock()

        with patch("app.routers.websocket.redis") as mock_redis:
            mock_redis.get.return_value = None

            with patch("app.routers.websocket.jwt.decode") as mock_jwt:
                mock_jwt.return_value = {"sub": "1", "scopes": ["client"]}

                with patch("app.routers.websocket.get_user") as mock_get_user:
                    mock_user = MagicMock()
                    mock_user.id = 1
                    mock_user.is_active = False  # Inactive user
                    mock_user.verified = True
                    mock_get_user.return_value = mock_user

                    result = await authenticate_websocket_user(
                        mock_websocket, user_id=1, db=mock_db, token="valid_token"
                    )

                    assert result is None

    @pytest.mark.asyncio
    async def test_auth_fails_for_unverified_user(self):
        """Test that authentication fails for unverified users."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.headers = {}
        mock_db = AsyncMock()

        with patch("app.routers.websocket.redis") as mock_redis:
            mock_redis.get.return_value = None

            with patch("app.routers.websocket.jwt.decode") as mock_jwt:
                mock_jwt.return_value = {"sub": "1", "scopes": ["client"]}

                with patch("app.routers.websocket.get_user") as mock_get_user:
                    mock_user = MagicMock()
                    mock_user.id = 1
                    mock_user.is_active = True
                    mock_user.verified = False  # Unverified user
                    mock_get_user.return_value = mock_user

                    result = await authenticate_websocket_user(
                        mock_websocket, user_id=1, db=mock_db, token="valid_token"
                    )

                    assert result is None

    @pytest.mark.asyncio
    async def test_auth_fails_for_otp_token(self):
        """Test that authentication fails for OTP tokens."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.headers = {}
        mock_db = AsyncMock()

        with patch("app.routers.websocket.redis") as mock_redis:
            mock_redis.get.return_value = None

            with patch("app.routers.websocket.jwt.decode") as mock_jwt:
                mock_jwt.return_value = {"sub": "1", "scopes": ["otp"]}  # OTP token

                with patch("app.routers.websocket.get_user") as mock_get_user:
                    mock_user = MagicMock()
                    mock_user.id = 1
                    mock_user.is_active = True
                    mock_user.verified = True
                    mock_get_user.return_value = mock_user

                    result = await authenticate_websocket_user(
                        mock_websocket, user_id=1, db=mock_db, token="otp_token"
                    )

                    assert result is None


class TestGlobalConnectionManager:
    """Tests to verify the global connection manager is properly initialized."""

    def test_ws_manager_is_initialized(self):
        """Test that the global ws_manager is properly initialized."""
        assert ws_manager is not None
        assert isinstance(ws_manager, WebSocketConnectionManager)
        assert isinstance(ws_manager.active_connections, dict)
