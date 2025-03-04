from sqlmodel import Field, SQLModel, Relationship
from passlib.context import CryptContext
from pydantic import EmailStr
from uuid import UUID, uuid4
from datetime import datetime, timezone
from db.database import AutomapBase
from enum import Enum
from typing import Optional


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

class RoleEnum(str, Enum):
    accountant = "accountant"
    manager = "manager"
    moderator = "moderator"
    support = "support"

class AdminStatus(str, Enum):
    active = "active"
    inactive = "inactive"
class AdminUser(CustomBaseModel, table=True):
    __tablename__ = "admin_users"
    email: EmailStr
    firstname: str
    lastname: str
    role: RoleEnum = Field(default=RoleEnum.manager)
    password: str
    is_default_password: bool = Field(default=True)
    is_active: bool = Field(default=True)
    last_login: datetime | None = Field(default=None)
    password_reset: Optional["AdminPasswordResetToken"] = Relationship(back_populates="user")

    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes a password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifies a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)


class AdminPasswordResetToken(CustomBaseModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: UUID = Field(default=None, foreign_key="admin_users.id", unique=True)
    is_valid: bool = Field(default=True)
    token: str
    expire: datetime
    user: Optional[AdminUser] = Relationship(back_populates="password_reset")

    