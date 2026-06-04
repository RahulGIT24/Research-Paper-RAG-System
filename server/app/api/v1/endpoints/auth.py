from fastapi import APIRouter,Depends,status,Response, Request
from sqlalchemy.orm import Session
from shared_lib.db.session import get_db
from shared_lib.pydantic_models.models import SignUp, Login, ForgotPasswordRequest, ResetPasswordRequest
from shared_lib.models import User
from shared_lib.core.exceptions import BaseAPIException
import bcrypt
import jwt
from datetime import datetime, timedelta
from shared_lib.pydantic_models.models import EmailJob
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, InvalidTokenError
from shared_lib.core.config import settings
from shared_lib.infra.queue import send_email
from app.middleware.auth import get_current_user
from jwt import ExpiredSignatureError, InvalidTokenError

router = APIRouter()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = 'HS256'

def generate_token(type:str,time=15,**kwargs):
    payload = {
        **kwargs,
        "type": type,
        "exp": datetime.utcnow() + timedelta(minutes=time)
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/signup",status_code=status.HTTP_201_CREATED)
async def signup(user:SignUp,db:Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user is not None:
        raise BaseAPIException(status_code=status.HTTP_409_CONFLICT,message="User already exists")
    hashed_pass_bytes = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    hashed_pass_string = hashed_pass_bytes.decode('utf-8')
    token = generate_token("verification",time=15,email=user.email)
    try:
        new_user = User(name=user.name,email=user.email,password_hash=hashed_pass_string,is_active=True,is_verified=False,verification_token=token)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        job_payload:EmailJob = {
            "email_address":user.email,
            "type":'verification',
            "token":token
        }
        await send_email(job_payload)
    except Exception as e:
        print(e)
        db.rollback()
        raise BaseAPIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An error occurred while creating the account"
        )
    return {
            "message": "User created successfully",
            "user_id": new_user.id,
            "email": new_user.email
        }

@router.post("/signin", status_code=status.HTTP_200_OK)
async def signin(user: Login, response:Response, db: Session = Depends(get_db)):
    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )
    if existing_user is None:
        raise BaseAPIException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="User not exists with this email id"
        )
    try:
        if not bcrypt.checkpw(
            user.password.encode("utf-8"),
            existing_user.password_hash.encode("utf-8")
        ):
            raise BaseAPIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid Credentials"
            )
        if not existing_user.is_verified:
            existing_token = existing_user.verification_token

            if existing_token:
                try:
                    jwt.decode(
                        existing_token,
                        SECRET_KEY,
                        algorithms=[ALGORITHM]
                    )

                    return {
                        "message": "Verification email already sent. Please check your inbox."
                    }

                except ExpiredSignatureError:
                    pass

                except InvalidTokenError:
                    pass
            token = generate_token(
                "verification",
                time=15,
                email=existing_user.email
            )
            existing_user.verification_token = token
            db.commit()
            db.refresh(existing_user)
            job_payload:EmailJob = {
                "email_address":user.email,
                "type":'verification',
                "token":token
            }
            await send_email(job_payload)
            return {
                "message": "User not verified, verification email sent"
            }
        access_token = generate_token(
            "access",
            time=15,
            email=existing_user.email
        )
        refresh_token = generate_token(
            "refresh",
            time=7 * 24 * 60,
            email=existing_user.email
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=15 * 60
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=7 * 24 * 60 * 60
        )
        return {
            "message": "Logged In Successfully"
        }
    except BaseAPIException as e:
        raise e
    except Exception:
        db.rollback()
        raise BaseAPIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An error occurred while signing in"
        )

@router.get("/verify",status_code=status.HTTP_200_OK)
def verify(token:str,db:Session = Depends(get_db)):
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        email = data.get('email')
        type = data.get('type')
        if email is None:
            raise BaseAPIException(status_code=status.HTTP_403_FORBIDDEN,message="Invalid Token")
        if type != 'verification':
            raise BaseAPIException(status_code=status.HTTP_403_FORBIDDEN,message="Invalid Token")
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user is None:
            raise BaseAPIException(status_code=status.HTTP_404_NOT_FOUND,message="User not found")
        if existing_user.is_verified == True:
            return {
                "message":"Already Verified"
            }
        existing_user.is_verified = True
        existing_user.verification_token = None
        db.commit()
        db.refresh(existing_user)
        return {
            "message":"Account Verified Successfully!!"
        }
    except BaseAPIException as e:
        raise e
    except ExpiredSignatureError:
        raise BaseAPIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Token Expired"
        )
    except (InvalidSignatureError, InvalidTokenError):
        raise BaseAPIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Invalid Token"
        )
    except Exception as  e:
        db.rollback()
        raise BaseAPIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An error occurred while while verifying the account"
        )

@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token is None:
        raise BaseAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Refresh token missing"
        )
    try:
        payload = jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        if payload.get("type") != "refresh":
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
        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )
        if existing_user is None:
            raise BaseAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found"
            )
        if not existing_user.is_active:
            raise BaseAPIException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="User account inactive"
            )
        new_access_token = generate_token(
            "access",
            time=15,
            email=existing_user.email
        )
        new_refresh_token = generate_token(
            "refresh",
            time=7 * 24 * 60,
            email=existing_user.email
        )
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,  
            samesite="none",
            max_age=15 * 60
        )
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,  
            samesite="none",
            max_age=7 * 24 * 60 * 60
        )
        return {
            "message": "Tokens refreshed successfully"
        }

    except ExpiredSignatureError:
        raise BaseAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Refresh token expired"
        )
    except InvalidTokenError:
        raise BaseAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid refresh token"
        )
    except BaseAPIException as e:
        raise e
    except Exception:
        raise BaseAPIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An error occurred while refreshing tokens"
        )

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )
    if existing_user is None:
        raise BaseAPIException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="User not found"
        )
    try:
        forgot_password_token = generate_token(
            "forgot_password",
            time=15,
            email=existing_user.email
        )
        existing_user.forgot_password_token = forgot_password_token
        db.commit()
        db.refresh(existing_user)
        # TODO:
        # send forgot password email here
        return {
            "message": "Forgot password email sent successfully"
        }
    except BaseAPIException as e:
        raise e
    except Exception:
        db.rollback()
        raise BaseAPIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An error occurred while generating forgot password token"
        )

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            data.token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        if payload.get("type") != "forgot_password":
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
        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )
        if existing_user is None:
            raise BaseAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found"
            )
        if existing_user.forgot_password_token != data.token:
            raise BaseAPIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid reset token"
            )
        hashed_password = bcrypt.hashpw(
            data.new_password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")
        existing_user.password_hash = hashed_password
        existing_user.forgot_password_token = None
        db.commit()
        db.refresh(existing_user)
        return {
            "message": "Password reset successfully"
        }
    except ExpiredSignatureError:
        raise BaseAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Reset token expired"
        )
    except InvalidTokenError:
        raise BaseAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid reset token"
        )
    except BaseAPIException as e:
        raise e
    except Exception:
        db.rollback()
        raise BaseAPIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An error occurred while resetting password"
        )

@router.post("/logout")
def logout(
    response: Response, 
    current_user = Depends(get_current_user)
):
    """
    Logs out the user by clearing the authentication cookies.
    """
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,  
        samesite="none" 
    )

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="none" 
    )

    return {"message": "Logged out successfully"}