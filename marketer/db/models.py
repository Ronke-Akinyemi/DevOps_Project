from sqlmodel import Field, SQLModel, Relationship
from passlib.context import CryptContext
from pydantic import EmailStr
from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from decimal import Decimal


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
class CustomBaseModel(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Overriding the __init__ method to automatically update 'updated_at' on updates
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure updated_at is set whenever a new object is created or updated
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc)
    
    # You can manually manage update logic when saving
    def update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)

class Marketer(CustomBaseModel, table=True):
    __tablename__ = "marketer"  # Match Django's db_table name
    name: str
    phone: Optional[str] = Field(default=None, max_length=15, unique=True)
    email: str = Field(max_length=255, index=True, unique=True)
    address: str
    qualification: str
    sales_experience: bool
    gender: str
    password: str = Field(max_length=500)
    is_default_password: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    is_approved: bool = Field(default=False)
    is_active: bool = Field(default=True)
    balance: Decimal = Field(..., max_digits=10, decimal_places=2)
    last_login: Optional[datetime] = Field(default=None)
    referral_code: str = Field(max_length=20, unique=True)
    password_reset: Optional["MarketterPasswordResetToken"] = Relationship(back_populates="user")

    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes a password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifies a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)


class MarketterPasswordResetToken(CustomBaseModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: UUID = Field(default=None, foreign_key="marketer.id", unique=True)
    is_valid: bool = Field(default=True)
    token: str
    expire: datetime
    user: Optional[Marketer] = Relationship(back_populates="password_reset")

    