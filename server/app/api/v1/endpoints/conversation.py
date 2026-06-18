from fastapi import APIRouter,Depends
from app.middleware.auth import get_current_user
from shared_lib.db.session import get_db
from sqlalchemy.orm import Session
from shared_lib.core.exceptions import BaseAPIException
from shared_lib.models.conversation import Conversation
from shared_lib.models.messages import Messages
# from shared_lib.pydantic_models.models import ConversationResponse
from typing import List
from pydantic import BaseModel

class ConversationModel(BaseModel):
    name:str

router = APIRouter()

# paginated route
@router.get("/")
def get_all_conversations_for_user(page: int = 1, limit: int = 10,db:Session=Depends(get_db),user=Depends(get_current_user)):
    try:
        offset = (page - 1) * limit
        user_conversations = (
            db.query(Conversation)
            .filter(Conversation.user_id == user["id"])
            .order_by(Conversation.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return {
            "conversations":[
            {
                "id":c.id,
                "name":c.name,
                "created_at":c.created_at
            }
            for c in user_conversations
            ]
        }
    except:
        raise BaseAPIException(status_code=500,message="Internal Server Error")

@router.get("/messages")
def get_all_messages_of_conversation(conversation_id:str,db:Session=Depends(get_db),user=Depends(get_current_user)):
    try:
        user_conversation = (
            db.query(Conversation)
            .filter(Conversation.user_id == user["id"], Conversation.id == conversation_id)
            .first()
        )
        if not user_conversation:
            raise BaseAPIException(status_code=404,message="Conversation not found")
        messages = (
            db.query(Messages)
            .filter(Messages.conversation_id == conversation_id)
            .order_by(Messages.created_at.asc())
            .all()
        )
        return {
            "messages":[
            {
                "id":c.id,
                "role":c.role,
                "content":c.content,
                "created_at":c.created_at
            }
            for c in messages
            ]
        }
    except BaseAPIException:
        raise
    except Exception as e:
        print(e)
        raise BaseAPIException(status_code=500,message="Internal Server Error")

# create a conversation first
@router.post("/create")
def create_conversation(req:ConversationModel,db:Session=Depends(get_db),user=Depends(get_current_user)):
    user_id = user['id']
    try:
        new_conversation = Conversation(name=req.name,user_id=user_id)
        db.add(new_conversation)
        db.commit()
        db.flush()
        return {
            "message":"Conversation created succcessfully",
            "conversation_id":str(new_conversation.id)
        }
    except:
        db.rollback()
        raise BaseAPIException(status_code=500,message="Internal Server Error")