from pydantic import BaseModel
from typing import Optional, List
from db.models import RoleEnum, AdminStatus
from uuid import UUID
from datetime import datetime

class AdminListResponse(BaseModel):
    id: UUID
    firstname: str
    lastname: str
    email: str
    is_active: bool
    role: str

class AdminUpdateStaffRequest(BaseModel):
    status: Optional[AdminStatus]
    role: Optional[RoleEnum] = RoleEnum.manager