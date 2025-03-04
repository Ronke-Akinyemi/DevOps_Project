from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
class MarketerCreate(BaseModel):
    email: EmailStr
    name: str
    phone: str
    address: str
    qualification: str
    sales_experience: bool
    gender: Gender
    password: str

class MarketerResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    phone: str
    address: str
    qualification: str
    created_at: datetime
    is_active: bool
    gender: Gender
    balance: Decimal
    referral_code: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
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