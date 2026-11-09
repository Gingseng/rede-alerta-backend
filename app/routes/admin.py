from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from .. import crud, schemas
from ..auth import get_current_admin
from ..case_social import publish_case_to_facebook, publish_case_to_instagram
from ..social import mark_configuration_pending, platform_configuration, publish_social_once


router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/instagram/status")
def instagram_status(
    admin: str = Depends(get_current_admin)
):
    platforms = platform_configuration()
    instagram = platforms["instagram"]

    return {
        **instagram,
        "platforms": platforms,
    }


@router.get("/pending", response_model=list[schemas.AdminMissingCaseResponse])
def list_pending_cases(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    return crud.get_pending_cases(db)


@router.get("/cases", response_model=list[schemas.AdminMissingCaseResponse])
def list_all_cases(
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    if status and status != "all":
        return crud.get_cases_by_status(db, status)

    return crud.get_all_cases(db)


@router.patch("/{case_id}/publish", response_model=schemas.AdminMissingCaseResponse)
def publish_case(
    case_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    db_case = crud.publish_case(db, case_id)
    if not db_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")

    platforms = platform_configuration()
    for platform, callback in (
        ("instagram", publish_case_to_instagram),
        ("facebook", publish_case_to_facebook),
    ):
        configuration = platforms[platform]
        if configuration["ready"]:
            publish_social_once(db, db_case, platform, callback)
        else:
            mark_configuration_pending(db, db_case.id, platform, configuration["message"])

    return db_case


@router.post("/{case_id}/instagram/publish")
def manual_publish_case_to_instagram(
    case_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    db_case = crud.get_case_by_id(db, case_id)
    if not db_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")

    try:
        if db_case.status != "published":
            raise ValueError("O caso precisa estar publicado antes do envio social.")
        instagram = platform_configuration()["instagram"]
        if not instagram["ready"]:
            publication = mark_configuration_pending(db, db_case.id, "instagram", instagram["message"])
            return {"success": False, "message": publication.last_error, "social_status": publication.status}
        publication = publish_social_once(db, db_case, "instagram", publish_case_to_instagram)
        return {
            "success": publication.status == "published",
            "message": "Postagem enviada ao Instagram com sucesso." if publication.status == "published" else "Publicação não confirmada; não será repetida automaticamente.",
            "social_status": publication.status,
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao publicar no Instagram: {str(e)}"
        )


@router.post("/{case_id}/facebook/publish")
def manual_publish_case_to_facebook(
    case_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    db_case = crud.get_case_by_id(db, case_id)
    if not db_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    if db_case.status != "published":
        raise HTTPException(status_code=400, detail="O caso precisa estar publicado antes do envio social.")
    facebook = platform_configuration()["facebook"]
    if not facebook["ready"]:
        publication = mark_configuration_pending(db, db_case.id, "facebook", facebook["message"])
        return {"success": False, "message": publication.last_error, "social_status": publication.status}
    publication = publish_social_once(db, db_case, "facebook", publish_case_to_facebook)
    return {
        "success": publication.status == "published",
        "message": "Postagem enviada ao Facebook com sucesso." if publication.status == "published" else "Publicação não confirmada; não será repetida automaticamente.",
        "social_status": publication.status,
    }


@router.patch("/{case_id}/found", response_model=schemas.AdminMissingCaseResponse)
def mark_case_found(
    case_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    db_case = crud.mark_case_as_found(db, case_id)
    if not db_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    return db_case


@router.patch("/{case_id}/reject", response_model=schemas.AdminMissingCaseResponse)
def reject_case(
    case_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    db_case = crud.reject_case(db, case_id)
    if not db_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    return db_case
