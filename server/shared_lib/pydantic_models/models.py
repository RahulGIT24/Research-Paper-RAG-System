from pydantic import BaseModel,EmailStr, Field

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
    filepath:str
    uploaded_by:str
    status:str
    ext:str
    filename:str

class DeleteJob(BaseModel):
    document_id: str
    file_path: str

from typing import Literal
class EmailJob(BaseModel):
    email_address: str
    token: str
    type:Literal["forgot-password","verification"]