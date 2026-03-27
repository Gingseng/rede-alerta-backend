from sqlalchemy.orm import Session
from . import models, schemas


def create_case(db: Session, case: schemas.MissingCaseCreate):
    db_case = models.MissingCase(**case.model_dump())
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case


def get_public_cases(db: Session):
    return (
        db.query(models.MissingCase)
        .filter(models.MissingCase.status == "publicado")
        .order_by(models.MissingCase.created_at.desc())
        .all()
    )


def get_pending_cases(db: Session):
    return (
        db.query(models.MissingCase)
        .filter(models.MissingCase.status == "pendente")
        .order_by(models.MissingCase.created_at.desc())
        .all()
    )


def get_case_by_id(db: Session, case_id: int):
    return db.query(models.MissingCase).filter(models.MissingCase.id == case_id).first()


def update_case_status(db: Session, case_id: int, status: str):
    db_case = get_case_by_id(db, case_id)
    if not db_case:
        return None
    db_case.status = status
    db.commit()
    db.refresh(db_case)
    return db_case

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