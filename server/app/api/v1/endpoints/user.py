from fastapi import APIRouter,Depends
from app.middleware.auth import get_current_user

router = APIRouter()

@router.get("/")
def get_user(user=Depends(get_current_user)):
    return {k:v for k, v in user.items() if k != "id"}