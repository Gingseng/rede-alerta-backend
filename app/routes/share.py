from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import NewsPost

router = APIRouter(prefix="/share", tags=["share"])

FRONTEND_URL = "https://www.redealerta.ong.br"
DEFAULT_IMAGE = "https://www.redealerta.ong.br/og-default.jpg"


def resolve_image_url(image_url: str | None) -> str:
    if not image_url:
        return DEFAULT_IMAGE

    if image_url.startswith("http://") or image_url.startswith("https://"):
        return image_url

    normalized = image_url if image_url.startswith("/") else f"/{image_url}"
    return f"{FRONTEND_URL}{normalized}"


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
    description = post.summary or (
        post.content[:160] if post.content else "Publicação do Rede Alerta"
    )
    image = resolve_image_url(post.cover_image_url)
    public_url = f"{FRONTEND_URL}/informacoes/{post.slug}"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <title>{title}</title>
    <meta name="description" content="{description}" />
    <meta name="robots" content="index,follow" />
    <link rel="canonical" href="{public_url}" />

    <meta property="og:type" content="article" />
    <meta property="og:site_name" content="Rede Alerta" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{description}" />
    <meta property="og:url" content="{public_url}" />
    <meta property="og:image" content="{image}" />
    <meta property="og:image:secure_url" content="{image}" />
    <meta property="og:image:alt" content="{title}" />

    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{title}" />
    <meta name="twitter:description" content="{description}" />
    <meta name="twitter:image" content="{image}" />

    <meta http-equiv="refresh" content="0; url={public_url}" />
    <script>
      window.location.replace("{public_url}");
    </script>
  </head>
  <body>
    <p>Redirecionando...</p>
    <p><a href="{public_url}">Clique aqui se não for redirecionado.</a></p>
  </body>
</html>"""

    return HTMLResponse(content=html)