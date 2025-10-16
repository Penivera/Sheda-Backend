from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.models.chat import ChatMessage
from app.models.user import BaseUser
from app.schemas.chat import ChatMessageSchema
from app.schemas.user_schema import UserShow
from typing import Dict
from core.dependecies import DBSession
from app.services.user_service import ActiveUser,ActiveVerifiedWSUser
from typing import List
from sqlalchemy.future import select
from sqlalchemy.engine import Result
from core.logger import logger
from core.configs import settings
import json

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[Dict[int, WebSocket]] = []

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections.append({"user_id": user_id, "websocket": websocket}) # type: ignore

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [
            conn for conn in self.active_connections if conn["websocket"] != websocket # type: ignore
        ]

    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to a specific user by ID"""
        for conn in self.active_connections:
            if conn["user_id"] == user_id:
                await conn["websocket"].send_json(message)
                break  # stop after sending to first matching user

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection["websocket"].send_text(message) # type: ignore
    


manager = ConnectionManager()



@router.websocket("/ws")
async def websocket_chat(
    websocket: WebSocket,
    current_user: ActiveVerifiedWSUser,
    db: DBSession,
):
    if not current_user:
        logger.info("User not found")
        return  # user was invalid, websocket already closed in dependency

    await manager.connect(websocket, current_user.id)
    current_user = UserShow.model_validate(current_user)

    try:
        while True:
            try:
                data = await websocket.receive_json()
            except Exception:
                await websocket.send_text("Invalid JSON received")
                continue

            sender_id = current_user.id
            receiver_id = data.get("receiver_id")
            message = data.get("message")

            if not all([sender_id, receiver_id, message]):
                await websocket.send_text("Missing fields in message")
                continue

            # Store in DB
            chat_message = ChatMessageSchema(
                sender_id=sender_id, receiver_id=receiver_id, message=message
            )
            db_message = ChatMessage(**chat_message.model_dump(exclude_unset=True))
            db.add(db_message)
            await db.commit()
            await db.refresh(db_message)
            
        
            
            sender_info = {
                "id": sender_id,
                "username": current_user.username,
                "avatar_url": current_user.profile_pic,
                }
            payload = {
                "id": db_message.id,
                "sender_info": sender_info,
                "receiver_id": db_message.receiver_id,
                "message": db_message.message,
                "created_at": db_message.timestamp.isoformat() if db_message.timestamp else None,
                }


            await manager.send_personal_message(payload, receiver_id)


    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get(
    "/chat-history",
    response_model=List[ChatMessageSchema],
    status_code=status.HTTP_200_OK,
)
async def chat_history(current_user: ActiveUser, db: DBSession):
    query = select(ChatMessage).where(ChatMessage.sender_id == current_user.id)
    result: Result = await db.execute(query)
    chats = result.scalars().all()
    return chats
