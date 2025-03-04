from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class UserResponse(BaseModel):
    id: UUID
    name: str
    phone: str
    email:str
    is_active: bool
    subscription: str | None
    subscription_start_date: datetime | None
    subscription_end_date: datetime | None
    created_at: datetime


class BusinessResponse(BaseModel):
    id: UUID
    name: str
    street: str
class SingleUserResponse(BaseModel):
    id: UUID
    firstname: str
    lastname: str
    phone: str
    email: str
    is_active: bool
    profile_picture: str
    created_at: datetime
    subscription: str
    subscription_start_date: datetime | None
    subscription_end_date: datetime | None
    business: List[BusinessResponse]
