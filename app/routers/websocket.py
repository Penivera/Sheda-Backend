"""
WebSocket service for real-time messaging.
Endpoint: /ws/{user_id}
Authentication: JWT/Token from query parameter or Sec-WebSocket-Protocol header
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Query
from typing import Dict, Optional, Annotated
from core.dependecies import DBSession
from core.logger import logger
from core.configs import settings, redis
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import ChatMessage
from app.models.user import BaseUser
from app.schemas.chat import ChatMessageSchema, UserInfoSchema
from app.schemas.user_schema import UserShow
from app.services.auth import get_user
from app.utils.enums import AccountTypeEnum
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError


router = APIRouter(tags=["WebSocket"])


class WebSocketConnectionManager:
    """Manages WebSocket connections and message routing."""

    def __init__(self):
        # Dictionary mapping user_id to their WebSocket connections
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> bool:
        """
        Accept a WebSocket connection and track it by user_id.
        Returns True if connection was successful.
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected: user_id={user_id}")
        return True

    def disconnect(self, user_id: int):
        """Remove a user's WebSocket connection from tracking."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected: user_id={user_id}")

    def is_connected(self, user_id: int) -> bool:
        """Check if a user is currently connected."""
        return user_id in self.active_connections

    async def send_personal_message(self, message: dict, user_id: int) -> bool:
        """
        Send a message to a specific user by their ID.
        Returns True if the message was sent, False if user is not connected.
        """
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
                return True
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                # Clean up broken connection
                self.disconnect(user_id)
                return False
        return False

    async def broadcast(self, message: dict, exclude_user_id: Optional[int] = None):
        """Broadcast a message to all connected users, optionally excluding one."""
        disconnected_users = []
        for user_id, websocket in self.active_connections.items():
            if exclude_user_id and user_id == exclude_user_id:
                continue
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected_users.append(user_id)

        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)

    def get_connected_users(self) -> list[int]:
        """Get list of all currently connected user IDs."""
        return list(self.active_connections.keys())


# Global connection manager instance
ws_manager = WebSocketConnectionManager()


async def authenticate_websocket_user(
    websocket: WebSocket,
    user_id: int,
    db: AsyncSession,
    token: Optional[str] = None,
) -> Optional[BaseUser]:
    """
    Authenticate a WebSocket connection using JWT token.
    Token can be provided via:
    1. Query parameter (?token=...)
    2. Sec-WebSocket-Protocol header

    Returns the authenticated user or None if authentication fails.
    """
    # Try to get token from Sec-WebSocket-Protocol header if not provided via query
    if not token:
        protocols = websocket.headers.get("sec-websocket-protocol", "")
        if protocols:
            # Token might be in the protocol list
            protocol_list = [p.strip() for p in protocols.split(",")]
            for protocol in protocol_list:
                if protocol.startswith("Bearer."):
                    token = protocol[7:]  # Remove "Bearer." prefix
                    break
                elif not protocol.lower() in ["chat", "websocket"]:
                    # Assume it's a token if not a standard protocol name
                    token = protocol
                    break

    if not token:
        logger.warning(f"WebSocket auth failed: No token provided for user_id={user_id}")
        return None

    # Check if token is blacklisted
    is_blacklisted = await redis.get(settings.BLACKLIST_PREFIX.format(token))
    if is_blacklisted:
        logger.warning(f"WebSocket auth failed: Token is blacklisted for user_id={user_id}")
        return None

    try:
        payload: dict = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        identifier = payload.get("sub")
        if not identifier:
            logger.warning(f"WebSocket auth failed: No subject in token for user_id={user_id}")
            return None

        token_scopes = payload.get("scopes", [])

        # Determine account type from scopes
        account_type = AccountTypeEnum.client
        if AccountTypeEnum.agent.value in token_scopes:
            account_type = AccountTypeEnum.agent

        # Fetch user from database
        user = await get_user(str(identifier), db, account_type)

        if not user:
            logger.warning(f"WebSocket auth failed: User not found for identifier={identifier}")
            return None

        # Verify user_id matches
        if user.id != user_id:
            logger.warning(
                f"WebSocket auth failed: user_id mismatch (token={user.id}, path={user_id})"
            )
            return None

        if not user.is_active:
            logger.warning(f"WebSocket auth failed: User {user_id} is inactive")
            return None

        if not user.verified:
            logger.warning(f"WebSocket auth failed: User {user_id} is not verified")
            return None

        # Reject OTP tokens
        if "otp" in token_scopes:
            logger.warning(f"WebSocket auth failed: OTP token not permitted for user_id={user_id}")
            return None

        logger.info(f"WebSocket auth successful for user: {user.email}")
        return user

    except ExpiredSignatureError:
        logger.warning(f"WebSocket auth failed: Token expired for user_id={user_id}")
        return None
    except InvalidTokenError as e:
        logger.error(f"WebSocket auth failed: Invalid token for user_id={user_id} - {e}")
        return None
    except Exception as e:
        logger.error(f"WebSocket auth failed: Unexpected error for user_id={user_id} - {e}")
        return None


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: Annotated[Optional[str], Query()] = None,
):
    """
    WebSocket endpoint for real-time messaging.

    Connection:
    - Connect to /ws/{user_id}?token={jwt_token}
    - Or use Sec-WebSocket-Protocol header with the JWT token

    Authentication:
    - JWT token is required for authentication
    - Returns 401/403 for failed authentication during handshake

    Message Format (incoming):
    {
        "receiver_id": int,
        "message": str,
        "property_id": int (optional)
    }

    Message Format (outgoing):
    {
        "id": int,
        "sender_info": {
            "id": int,
            "username": str,
            "avatar_url": str
        },
        "receiver_id": int,
        "message": str,
        "created_at": str (ISO format),
        "property_id": int (optional)
    }
    """
    # Get database session
    async for db in get_db():
        try:
            # Authenticate the user
            user = await authenticate_websocket_user(websocket, user_id, db, token)

            if not user:
                # Authentication failed - close with policy violation code
                # This is equivalent to 401/403 for WebSocket
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            # Connect and track the session
            await ws_manager.connect(websocket, user_id)

            # Build user info for messages
            sender_info = {
                "id": user.id,
                "username": user.username,
                "avatar_url": user.profile_pic,
            }

            try:
                while True:
                    # Wait for incoming messages
                    try:
                        data = await websocket.receive_json()
                    except Exception:
                        await websocket.send_json({"error": "Invalid JSON received"})
                        continue

                    receiver_id = data.get("receiver_id")
                    message = data.get("message")
                    property_id = data.get("property_id")

                    # Validate required fields
                    if not receiver_id or not message:
                        await websocket.send_json(
                            {"error": "Missing required fields: receiver_id, message"}
                        )
                        continue

                    # Store message in database
                    chat_message = ChatMessage(
                        sender_id=user_id,
                        receiver_id=receiver_id,
                        message=message,
                        property_id=property_id,
                        is_read=False,
                    )
                    db.add(chat_message)
                    await db.commit()
                    await db.refresh(chat_message)

                    # Build outgoing message payload
                    payload = {
                        "id": chat_message.id,
                        "sender_info": sender_info,
                        "receiver_id": chat_message.receiver_id,
                        "message": chat_message.message,
                        "created_at": (
                            chat_message.timestamp.isoformat()
                            if chat_message.timestamp
                            else None
                        ),
                        "property_id": chat_message.property_id,
                    }

                    # Send to receiver if connected
                    sent = await ws_manager.send_personal_message(payload, receiver_id)

                    # Send confirmation back to sender
                    await websocket.send_json(
                        {
                            "status": "sent",
                            "delivered": sent,
                            "message_id": chat_message.id,
                        }
                    )

            except WebSocketDisconnect:
                ws_manager.disconnect(user_id)
                logger.info(f"WebSocket disconnected for user_id={user_id}")

        except Exception as e:
            logger.error(f"WebSocket error for user_id={user_id}: {e}")
            ws_manager.disconnect(user_id)
        finally:
            break  # Exit the async generator loop
