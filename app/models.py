from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .database import Base


class MissingCase(Base):
    __tablename__ = "missing_cases"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    age = Column(Integer, nullable=False)
    city = Column(String(120), nullable=False)
    state = Column(String(2), nullable=False)
    missing_date = Column(String(50), nullable=False)
    last_seen_clothes = Column(Text, nullable=True)
    physical_traits = Column(Text, nullable=True)
    case_description = Column(Text, nullable=True)
    police_report_number = Column(String(100), nullable=False)
    contact_name = Column(String(150), nullable=False)
    contact_phone = Column(String(30), nullable=False)
    photo_url = Column(String(300), nullable=True)

    # pending | published | found | rejected
    status = Column(String(30), nullable=False, default="pending", index=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class CaseTip(Base):
    __tablename__ = "case_tips"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, nullable=False, index=True)

    is_anonymous = Column(String(10), default="sim")
    reporter_name = Column(String(150), nullable=True)
    reporter_phone = Column(String(30), nullable=True)
    reporter_email = Column(String(150), nullable=True)

    message = Column(Text, nullable=False)
    status = Column(String(30), default="novo")

    created_at = Column(DateTime, default=datetime.utcnow)