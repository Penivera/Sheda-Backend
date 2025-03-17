from fastapi import APIRouter, WebSocket, WebSocketDisconnect,status
from app.models.chat import ChatMessage
from app.schemas.chat import ChatMessageSchema
from typing import Dict
from core.dependecies import DBSession
from app.services.user_service import ActiveUser
from typing import List
from sqlalchemy.future import select
from sqlalchemy.engine import Result

router = APIRouter(prefix='/chat',tags=['Chat'],)

# Store active connections
active_connections: Dict[int, WebSocket] = {}

@router.websocket("/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: int, db:DBSession,current_user=ActiveUser):
    await websocket.accept()
    active_connections[user_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_json()
            sender_id = data["sender_id"]
            receiver_id = data["receiver_id"]
            message = data["message"]
            
            # Store message in the database
            chat_message = ChatMessageSchema(sender_id=sender_id, receiver_id=receiver_id, message=message)
            db_message = ChatMessage(**chat_message.model_dump(exclude_unset=True))
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            # Send message to receiver if online
            if receiver_id in active_connections:
                await active_connections[receiver_id].send_json({
                    "sender_id": sender_id,
                    "message": message
                })
                
    except WebSocketDisconnect:
        del active_connections[user_id]


@router.get('/chat-history',response_model=List[ChatMessageSchema],status_code=status.HTTP_200_OK)
async def chat_history(current_user:ActiveUser,db:DBSession):
    query = select(ChatMessage).where(ChatMessage.sender_id == current_user.id)
    result:Result = db.execute(query)
    chats = result.scalars().all()
    return chats
    