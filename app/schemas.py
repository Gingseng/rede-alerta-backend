from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MissingCaseCreate(BaseModel):
    full_name: str
    age: int
    city: str
    state: str
    missing_date: str
    last_seen_clothes: Optional[str] = None
    physical_traits: Optional[str] = None
    case_description: Optional[str] = None
    police_report_number: str
    contact_name: str
    contact_phone: str
    photo_url: Optional[str] = None


class MissingCaseResponse(BaseModel):
    id: int
    full_name: str
    age: int
    city: str
    state: str
    missing_date: str
    last_seen_clothes: Optional[str] = None
    physical_traits: Optional[str] = None
    case_description: Optional[str] = None
    police_report_number: str
    contact_name: str
    contact_phone: str
    photo_url: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdminLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CaseTipCreate(BaseModel):
    case_id: int
    is_anonymous: str = "sim"
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None
    reporter_email: Optional[str] = None
    message: str


class CaseTipResponse(BaseModel):
    id: int
    case_id: int
    is_anonymous: str
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None
    reporter_email: Optional[str] = None
    message: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True