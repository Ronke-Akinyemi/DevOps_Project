from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class TransactionResponse(BaseModel):
    id: UUID
    user: str
    description: str | None
    amount: int
    status: str
    created_at: datetime

class MarketerResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    phone: str
    no_of_merchants: int
    total_earning: float