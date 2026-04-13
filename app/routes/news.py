from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import cloudinary.uploader

from app.database import get_db
from app import crud, schemas
from app.auth import get_current_admin
from app.cloudinary_config import *

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/public", response_model=list[schemas.NewsPostResponse])
def list_public_news(db: Session = Depends(get_db)):
    return crud.get_public_news(db)


@router.get("/public/{slug}", response_model=schemas.NewsPostResponse)
def get_public_news(slug: str, db: Session = Depends(get_db)):
    post = crud.get_public_news_by_slug(db, slug)
    if not post:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")
    return post


@router.get("/admin", response_model=list[schemas.NewsPostResponse])
def list_admin_news(
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin)
):
    return crud.get_all_news_admin(db)


@router.post("/admin", response_model=schemas.NewsPostResponse)
def create_news(
    title: str = Form(...),
    summary: Optional[str] = Form(None),
    content: str = Form(...),
    cover_image_url: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    status: str = Form("rascunho"),
    cover_image_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin)
):
    final_cover_url = cover_image_url

    if cover_image_file:
        try:
            result = cloudinary.uploader.upload(
                cover_image_file.file,
                folder="rede-alerta/news",
                resource_type="image"
            )
            final_cover_url = result.get("secure_url")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao enviar imagem da notícia: {str(e)}"
            )

    news_data = schemas.NewsPostCreate(
        title=title,
        summary=summary,
        content=content,
        cover_image_url=final_cover_url,
        category=category,
        status=status,
    )

    return crud.create_news(db, news_data)


@router.put("/admin/{post_id}", response_model=schemas.NewsPostResponse)
def update_news(
    post_id: int,
    title: Optional[str] = Form(None),
    summary: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    cover_image_url: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    cover_image_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin)
):
    final_cover_url = cover_image_url

    if cover_image_file:
        try:
            result = cloudinary.uploader.upload(
                cover_image_file.file,
                folder="rede-alerta/news",
                resource_type="image"
            )
            final_cover_url = result.get("secure_url")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao enviar imagem da notícia: {str(e)}"
            )

    news_data = schemas.NewsPostUpdate(
        title=title,
        summary=summary,
        content=content,
        cover_image_url=final_cover_url,
        category=category,
        status=status,
    )

    post = crud.update_news(db, post_id, news_data)
    if not post:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")
    return post


@router.delete("/admin/{post_id}")
def delete_news(
    post_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin)
):
    deleted = crud.delete_news(db, post_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")
    return {"message": "Notícia removida com sucesso"}