from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud, schemas
from app.auth import get_current_admin

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
    news: schemas.NewsPostCreate,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin)
):
    return crud.create_news(db, news)


@router.put("/admin/{post_id}", response_model=schemas.NewsPostResponse)
def update_news(
    post_id: int,
    news: schemas.NewsPostUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin)
):
    post = crud.update_news(db, post_id, news)
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