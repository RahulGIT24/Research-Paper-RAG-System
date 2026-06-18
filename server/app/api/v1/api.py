from fastapi import APIRouter
from app.api.v1.endpoints import auth,user,document,query,conversation

api_router = APIRouter()

api_router.include_router(auth.router,prefix="/auth",tags=["Authentication"])
api_router.include_router(user.router,prefix="/user",tags=["User"])
api_router.include_router(document.router,prefix="/document",tags=["Document"])
api_router.include_router(query.router,prefix="/query",tags=["Query"])
api_router.include_router(conversation.router,prefix="/conversation",tags=["Conversation"])