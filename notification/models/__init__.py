from pydantic import BaseModel, EmailStr
from typing import List, Dict

class SendSms(BaseModel):
    body: str
    to: str

class EmailRequest(BaseModel):
    email: EmailStr
    title: str
    message: str

class NotificationRequest(BaseModel):
    token: str
    title: str
    body: str
    data: dict = {}
class BulkNotificationRequest(BaseModel):
    tokens: List[str]
    title: str
    body: str
    data: Dict[str, str] = {}