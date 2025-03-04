from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class PlanRequest(BaseModel):
    name: str
    monthly: int
    quarterly: int
    biannually: int
    annually: int
    no_of_users: int
    no_of_attendants: int
    no_of_business: int

class SinglePlanResponse(BaseModel):
    id: int
    name: str | None
    monthly: int
    quarterly: int
    biannually: int
    annually: int
    no_of_users: int
    no_of_attendants: int
    no_of_business: int

class SinglePlanEditResponse(BaseModel):
    name: str | None = None
    monthly: int | None = None
    quarterly: int | None = None
    biannually: int | None = None
    annually: int | None = None
    no_of_users: int | None = None
    no_of_attendants: int | None = None
    no_of_business: int | None = None
