"""
WebSocket service for real-time messaging.
Endpoint: /ws/{user_id}
Authentication: JWT/Token from query parameter (?token=...) or Sec-WebSocket-Protocol header (Bearer.{token})
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from typing import Dict, Optional
from core.dependecies import DBSession
from core.logger import logger
from app.models.chat import ChatMessage
from app.services.user_service import ActiveVerifiedWSUser


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


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    current_user: ActiveVerifiedWSUser,
    db: DBSession,
):
    """
    WebSocket endpoint for real-time messaging.

    Authentication:
    - Connect with query param: /ws/{user_id}?token={jwt_token}
    - Or via Sec-WebSocket-Protocol header: Bearer.{jwt_token}

    Note: JWT token is required for authentication.
    Returns WS_1008_POLICY_VIOLATION (401/403 equivalent) for failed auth.

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
    if not current_user:
        logger.info("User not found or authentication failed")
        return  # user was invalid, websocket already closed in dependency

    # Verify user_id matches the authenticated user
    if current_user.id != user_id:
        logger.warning(f"WebSocket auth failed: user_id mismatch (token={current_user.id}, path={user_id})")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Connect and track the session
    await ws_manager.connect(websocket, user_id)

    # Build user info for messages
    sender_info = {
        "id": current_user.id,
        "username": current_user.username,
        "avatar_url": current_user.profile_pic,
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
