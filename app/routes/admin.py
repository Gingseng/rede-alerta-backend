import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..instagram_service import publish_image_to_instagram, is_instagram_configured
from ..database import get_db
from .. import crud, schemas
from ..auth import get_current_admin


router = APIRouter(prefix="/admin", tags=["admin"])

BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "").rstrip("/")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "").strip()


def build_case_caption(case):
    return f"""🚨 PESSOA DESAPARECIDA

{case.full_name}, {case.age} anos.
Última informação em {case.city}/{case.state} no dia {case.missing_date}.

{case.case_description or "Qualquer informação pode ser essencial para ajudar neste caso."}

Compartilhe esta publicação para ampliar o alcance.

#RedeAlerta #Desaparecidos #AjudeACompartilhar #CadaMinutoConta"""


def build_public_image_url(photo_url: Optional[str]) -> Optional[str]:
    if not photo_url:
        return None

    if photo_url.startswith("http://") or photo_url.startswith("https://"):
        return photo_url

    if not BACKEND_PUBLIC_URL:
        return None

    normalized_path = photo_url if photo_url.startswith("/") else f"/{photo_url}"
    return f"{BACKEND_PUBLIC_URL}{normalized_path}"


def publish_case_to_instagram(case):
    if not is_instagram_configured():
        raise ValueError("Instagram não configurado.")

    image_url = build_public_image_url(case.photo_url)
    if not image_url:
        raise ValueError("Imagem sem URL pública válida.")

    caption = build_case_caption(case)
    return publish_image_to_instagram(image_url=image_url, caption=caption)


@router.get("/instagram/status")
def instagram_status(
    admin: str = Depends(get_current_admin)
):
    configured = is_instagram_configured()

    ready = bool(configured and INSTAGRAM_ACCOUNT_ID and BACKEND_PUBLIC_URL)

    return {
        "configured": configured,
        "account_id": INSTAGRAM_ACCOUNT_ID if INSTAGRAM_ACCOUNT_ID else None,
        "backend_public_url": BACKEND_PUBLIC_URL if BACKEND_PUBLIC_URL else None,
        "ready": ready,
        "message": (
            "Instagram conectado e pronto para publicar."
            if ready
            else "Configuração incompleta para publicação automática."
        ),
    }


@router.get("/pending", response_model=list[schemas.MissingCaseResponse])
def list_pending_cases(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    return crud.get_pending_cases(db)


@router.get("/cases", response_model=list[schemas.MissingCaseResponse])
def list_all_cases(
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    if status and status != "all":
        return crud.get_cases_by_status(db, status)

    return crud.get_all_cases(db)


@router.patch("/{case_id}/publish", response_model=schemas.MissingCaseResponse)
def publish_case(
    case_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    db_case = crud.publish_case(db, case_id)
    if not db_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")

    try:
        publish_case_to_instagram(db_case)
    except Exception as e:
        # Não quebra a publicação do caso no sistema se o Instagram falhar
        print(f"Erro ao publicar no Instagram automaticamente: {e}")

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
        result = publish_case_to_instagram(db_case)
        return {
            "success": True,
            "message": "Postagem enviada ao Instagram com sucesso.",
            "instagram_result": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao publicar no Instagram: {str(e)}"
        )


@router.patch("/{case_id}/found", response_model=schemas.MissingCaseResponse)
def mark_case_found(
    case_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    db_case = crud.mark_case_as_found(db, case_id)
    if not db_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    return db_case


@router.patch("/{case_id}/reject", response_model=schemas.MissingCaseResponse)
def reject_case(
    case_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    db_case = crud.reject_case(db, case_id)
    if not db_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    return db_case