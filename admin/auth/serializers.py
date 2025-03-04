from pydantic import BaseModel, EmailStr
from typing import Optional
from db.models import RoleEnum
from datetime import datetime
from uuid import UUID

class AdminUserCreate(BaseModel):
    email: EmailStr
    firstname: str
    lastname: str
    role: Optional[RoleEnum] = RoleEnum.manager

class AdminUserResponse(BaseModel):
    id: UUID
    email: EmailStr
    firstname: str
    lastname: str
    role: str
    last_login: datetime | None
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    role: str
    name: str
    email: str

class TokenData(BaseModel):
    username: str | None = None

class LoginRequest(BaseModel):
    email: str
    password: str
class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangeDefaultPasswordRequest(BaseModel):
    email: str
    default_password: str
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ForgetPasswordRequest(BaseModel):
    email: str

class VerifyPasswordResetToken(BaseModel):
    email: str
    token: str

class ResetPasswordRequest(BaseModel):
    uid64: str
    password: str

class SuspendUser(BaseModel):
    status: bool