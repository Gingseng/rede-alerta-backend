from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, schemas
import os
import shutil
import uuid

router = APIRouter(prefix="/cases", tags=["cases"])

UPLOAD_DIR = "app/uploads"


@router.post("/", response_model=schemas.MissingCaseResponse)
def create_new_case(
    full_name: str = Form(...),
    age: int = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    missing_date: str = Form(...),
    last_seen_clothes: str = Form(None),
    physical_traits: str = Form(None),
    case_description: str = Form(None),
    police_report_number: str = Form(...),
    contact_name: str = Form(...),
    contact_phone: str = Form(...),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    photo_url = None

    if photo:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        extension = os.path.splitext(photo.filename)[1]
        filename = f"{uuid.uuid4().hex}{extension}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

        photo_url = f"/uploads/{filename}"

    case_data = schemas.MissingCaseCreate(
        full_name=full_name,
        age=age,
        city=city,
        state=state,
        missing_date=missing_date,
        last_seen_clothes=last_seen_clothes,
        physical_traits=physical_traits,
        case_description=case_description,
        police_report_number=police_report_number,
        contact_name=contact_name,
        contact_phone=contact_phone,
        photo_url=photo_url,
    )

    return crud.create_case(db, case_data)


@router.get("/public", response_model=list[schemas.MissingCaseResponse])
def list_public_cases(db: Session = Depends(get_db)):
    return crud.get_public_cases(db)


@router.get("/{case_id}", response_model=schemas.MissingCaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    db_case = crud.get_case_by_id(db, case_id)
    if not db_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    return db_case