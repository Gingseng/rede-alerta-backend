from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import NewsPost

router = APIRouter(prefix="/share", tags=["share"])

FRONTEND_URL = "https://redealerta.ong.br"
DEFAULT_IMAGE = "https://redealerta.ong.br/og-default.jpg"

@router.get("/news/{slug}", response_class=HTMLResponse)
def share_news(slug: str, db: Session = Depends(get_db)):
    post = (
        db.query(NewsPost)
        .filter(NewsPost.slug == slug, NewsPost.status == "publicado")
        .first()
    )

    if not post:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")

    title = post.title or "Rede Alerta"
    description = post.summary or (post.content[:160] if post.content else "Publicação do Rede Alerta")
    image = post.cover_image_url or DEFAULT_IMAGE
    public_url = f"{FRONTEND_URL}/informacoes/{post.slug}"

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
      <head>
        <meta charset="utf-8" />
        <title>{title}</title>
        <meta name="description" content="{description}" />

        <meta property="og:title" content="{title}" />
        <meta property="og:description" content="{description}" />
        <meta property="og:image" content="{image}" />
        <meta property="og:url" content="{public_url}" />
        <meta property="og:type" content="article" />
        <meta property="og:site_name" content="Rede Alerta" />

        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="{title}" />
        <meta name="twitter:description" content="{description}" />
        <meta name="twitter:image" content="{image}" />

        <meta http-equiv="refresh" content="0;url={public_url}" />
      </head>
      <body>
        <p>Redirecionando...</p>
      </body>
    </html>
    """
    return HTMLResponse(content=html)