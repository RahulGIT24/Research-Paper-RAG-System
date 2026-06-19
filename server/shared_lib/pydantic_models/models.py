from pydantic import BaseModel,EmailStr, Field
import uuid

class SignUp(BaseModel):
    name:str = Field(...,min_length=3,max_length=20)
    email:EmailStr
    password:str = Field(...,min_length=8,max_length=20)

class Login(BaseModel):
    email:EmailStr
    password:str = Field(...,min_length=8,max_length=20)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class JobData(BaseModel):
    id:str
    hash_id:str
    server_file_name:str
    filepath:str
    uploaded_by:str
    ext:str
    filename:str

class DeleteJob(BaseModel):
    document_id: str
    file_path: str
    document_hash_id:str

from typing import Literal
class EmailJob(BaseModel):
    email_address: str
    token: str
    type:Literal["forgot-password","verification"]

# class ConversationResponse(BaseModel):
#     id: int
#     name: str
#     created_at: datetime

#     class Config:
#         from_attributes = True