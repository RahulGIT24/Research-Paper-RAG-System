from fastapi import Request, Depends, status
from sqlalchemy.orm import Session
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidTokenError
)
import jwt
from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.core.exceptions import BaseAPIException

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")
    if token is None:
        raise BaseAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Access token missing"
        )
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        # Validate token type
        if payload.get("type") != "access":
            raise BaseAPIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid token type"
            )
        email = payload.get("email")
        if email is None:
            raise BaseAPIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid token payload"
            )
        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )
        if user is None:
            raise BaseAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found"
            )
        user_to_return = {k:v for k,v, in  user.__dict__.items() if k in {"id","name","email","is_active","is_verified","created_at"}}
        return user_to_return
    except ExpiredSignatureError:
        raise BaseAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Token expired"
        )
    except InvalidTokenError:
        raise BaseAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid token"
        )