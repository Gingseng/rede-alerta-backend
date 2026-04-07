from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime
import re
import unicodedata
from app import models, schemas

VALID_CASE_STATUSES = {"pending", "published", "found", "rejected"}


def create_case(db: Session, case: schemas.MissingCaseCreate):
    db_case = models.MissingCase(
        **case.model_dump(),
        status="pending"
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case


def get_public_cases(db: Session):
    return (
        db.query(models.MissingCase)
        .filter(models.MissingCase.status == "published")
        .order_by(models.MissingCase.created_at.desc())
        .all()
    )


def get_pending_cases(db: Session):
    return get_cases_by_status(db, "pending")


def get_all_cases(db: Session):
    return (
        db.query(models.MissingCase)
        .order_by(models.MissingCase.created_at.desc())
        .all()
    )


def get_cases_by_status(db: Session, status: str):
    if status not in VALID_CASE_STATUSES:
        return []

    return (
        db.query(models.MissingCase)
        .filter(models.MissingCase.status == status)
        .order_by(models.MissingCase.created_at.desc())
        .all()
    )


def get_case_by_id(db: Session, case_id: int):
    return (
        db.query(models.MissingCase)
        .filter(models.MissingCase.id == case_id)
        .first()
    )


def update_case_status(db: Session, case_id: int, status: str):
    if status not in VALID_CASE_STATUSES:
        return None

    db_case = get_case_by_id(db, case_id)
    if not db_case:
        return None

    db_case.status = status
    db.commit()
    db.refresh(db_case)
    return db_case


def publish_case(db: Session, case_id: int):
    """
    Publica o caso no sistema.
    Futuramente, este será o ponto ideal para acionar
    a rotina de publicação automática no Instagram.
    """
    return update_case_status(db, case_id, "published")


def mark_case_as_found(db: Session, case_id: int):
    return update_case_status(db, case_id, "found")


def reject_case(db: Session, case_id: int):
    return update_case_status(db, case_id, "rejected")


def create_tip(db: Session, tip: schemas.CaseTipCreate):
    db_tip = models.CaseTip(**tip.model_dump())
    db.add(db_tip)
    db.commit()
    db.refresh(db_tip)
    return db_tip


def get_tips_by_case(db: Session, case_id: int):
    return (
        db.query(models.CaseTip)
        .filter(models.CaseTip.case_id == case_id)
        .order_by(models.CaseTip.created_at.desc())
        .all()
    )


def get_all_tips(db: Session):
    return (
        db.query(models.CaseTip)
        .order_by(models.CaseTip.created_at.desc())
        .all()
    )
# CRUD para NewsPost
def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[-\s]+", "-", text)
    return text

def get_public_news(db):
    return (
        db.query(models.NewsPost)
        .filter(models.NewsPost.status == "publicado")
        .order_by(models.NewsPost.published_at.desc(), models.NewsPost.created_at.desc())
        .all()
    )


def get_public_news_by_slug(db, slug: str):
    return (
        db.query(models.NewsPost)
        .filter(
            models.NewsPost.slug == slug,
            models.NewsPost.status == "publicado"
        )
        .first()
    )


def get_all_news_admin(db):
    return db.query(models.NewsPost).order_by(models.NewsPost.created_at.desc()).all()


def create_news(db, news: schemas.NewsPostCreate):
    base_slug = slugify(news.title)
    slug = base_slug
    counter = 1

    while db.query(models.NewsPost).filter(models.NewsPost.slug == slug).first():
        counter += 1
        slug = f"{base_slug}-{counter}"

    published_at = datetime.utcnow() if news.status == "publicado" else None

    db_news = models.NewsPost(
        title=news.title,
        slug=slug,
        summary=news.summary,
        content=news.content,
        cover_image_url=news.cover_image_url,
        category=news.category,
        status=news.status,
        published_at=published_at,
    )

    db.add(db_news)
    db.commit()
    db.refresh(db_news)
    return db_news


def update_news(db, post_id: int, news: schemas.NewsPostUpdate):
    db_news = db.query(models.NewsPost).filter(models.NewsPost.id == post_id).first()
    if not db_news:
        return None

    update_data = news.model_dump(exclude_unset=True)

    if "title" in update_data and update_data["title"]:
        db_news.title = update_data["title"]

    if "summary" in update_data:
        db_news.summary = update_data["summary"]

    if "content" in update_data:
        db_news.content = update_data["content"]

    if "cover_image_url" in update_data:
        db_news.cover_image_url = update_data["cover_image_url"]

    if "category" in update_data:
        db_news.category = update_data["category"]

    if "status" in update_data:
        db_news.status = update_data["status"]
        if update_data["status"] == "publicado" and not db_news.published_at:
            db_news.published_at = datetime.utcnow()

    db.commit()
    db.refresh(db_news)
    return db_news


def delete_news(db, post_id: int):
    db_news = db.query(models.NewsPost).filter(models.NewsPost.id == post_id).first()
    if not db_news:
        return None

    db.delete(db_news)
    db.commit()
    return True