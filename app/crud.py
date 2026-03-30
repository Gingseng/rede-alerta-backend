from sqlalchemy.orm import Session
from . import models, schemas


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