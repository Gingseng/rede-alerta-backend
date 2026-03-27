from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, schemas
from ..auth import get_current_admin

router = APIRouter(prefix="/tips", tags=["tips"])


@router.post("/", response_model=schemas.CaseTipResponse)
def create_new_tip(tip: schemas.CaseTipCreate, db: Session = Depends(get_db)):
    return crud.create_tip(db, tip)


@router.get("/case/{case_id}", response_model=list[schemas.CaseTipResponse])
def list_case_tips(
    case_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    return crud.get_tips_by_case(db, case_id)


@router.get("/", response_model=list[schemas.CaseTipResponse])
def list_all_tips(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    return crud.get_all_tips(db)