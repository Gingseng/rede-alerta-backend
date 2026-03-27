from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, schemas
from ..auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/pending", response_model=list[schemas.MissingCaseResponse])
def list_pending_cases(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    return crud.get_pending_cases(db)


@router.patch("/{case_id}/publish", response_model=schemas.MissingCaseResponse)
def publish_case(
    case_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    db_case = crud.update_case_status(db, case_id, "publicado")
    if not db_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    return db_case


@router.patch("/{case_id}/found", response_model=schemas.MissingCaseResponse)
def mark_case_found(
    case_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    db_case = crud.update_case_status(db, case_id, "encontrado")
    if not db_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    return db_case


@router.patch("/{case_id}/reject", response_model=schemas.MissingCaseResponse)
def reject_case(
    case_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    db_case = crud.update_case_status(db, case_id, "rejeitado")
    if not db_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    return db_case