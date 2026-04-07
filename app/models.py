from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func


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

    
class NewsPost(Base):
    __tablename__ = "news_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    summary = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    cover_image_url = Column(String, nullable=True)
    category = Column(String, nullable=True)
    status = Column(String, default="rascunho", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)