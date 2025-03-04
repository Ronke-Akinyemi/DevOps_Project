from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from merchant.serializers import UserResponse

class MarketersResponse(BaseModel):
    id: UUID
    name: str
    phone: str
    email:str
    address:  str
    qualification: str
    sales_experience: bool
    gender: str
    is_verified: bool
    is_approved: bool
    is_active: bool
    balance: Decimal
    referral_code: str
    created_at: datetime


class SingleMarketerResponse(BaseModel):
    id: UUID
    name: str
    phone: str
    email:str
    address:  str
    qualification: str
    sales_experience: bool
    gender: str
    is_verified: bool
    is_approved: bool
    is_active: bool
    balance: Decimal
    referral_code: str
    created_at: datetime
    custommers: List[UserResponse]
