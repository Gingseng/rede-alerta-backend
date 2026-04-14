from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import NewsPost, MissingCase
import html

router = APIRouter(prefix="/share", tags=["share"])

FRONTEND_URL = "https://www.redealerta.ong.br"
API_BASE_URL = "https://rede-alerta-backendof.onrender.com"
DEFAULT_IMAGE = f"{FRONTEND_URL}/og-default.jpg"


def resolve_image_url(image_url: str | None) -> str:
    if not image_url:
        return DEFAULT_IMAGE

    if image_url.startswith("http://") or image_url.startswith("https://"):
        return image_url

    normalized = image_url if image_url.startswith("/") else f"/{image_url}"
    return f"{API_BASE_URL}{normalized}"


def build_share_html(
    *,
    title: str,
    description: str,
    image: str,
    public_url: str,
    redirect_url: str,
    og_type: str = "article",
) -> str:
    escaped_title = html.escape(title or "Rede Alerta")
    escaped_description = html.escape(description or "Rede Alerta")
    escaped_image = html.escape(image or DEFAULT_IMAGE)
    escaped_public_url = html.escape(public_url)
    escaped_redirect_url = html.escape(redirect_url)
    escaped_type = html.escape(og_type)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <title>{escaped_title}</title>
  <meta name="description" content="{escaped_description}" />
  <link rel="canonical" href="{escaped_public_url}" />

  <meta property="og:site_name" content="Rede Alerta" />
  <meta property="og:locale" content="pt_BR" />
  <meta property="og:type" content="{escaped_type}" />
  <meta property="og:title" content="{escaped_title}" />
  <meta property="og:description" content="{escaped_description}" />
  <meta property="og:url" content="{escaped_public_url}" />
  <meta property="og:image" content="{escaped_image}" />
  <meta property="og:image:secure_url" content="{escaped_image}" />
  <meta property="og:image:alt" content="{escaped_title}" />

  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{escaped_title}" />
  <meta name="twitter:description" content="{escaped_description}" />
  <meta name="twitter:image" content="{escaped_image}" />

  <meta http-equiv="refresh" content="0;url={escaped_redirect_url}" />
</head>
<body>
  <p>Redirecionando...</p>
  <p><a href="{escaped_redirect_url}">Clique aqui se não for redirecionado.</a></p>
</body>
</html>
"""


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
    description = (
        post.summary
        or (post.content[:160] if post.content else "Publicação do Rede Alerta")
    )
    image = resolve_image_url(post.cover_image_url)

    public_url = f"{FRONTEND_URL}/informacoes/{post.slug}"
    redirect_url = public_url

    html_content = build_share_html(
        title=title,
        description=description,
        image=image,
        public_url=public_url,
        redirect_url=redirect_url,
        og_type="article",
    )

    return HTMLResponse(content=html_content, status_code=200)


@router.get("/case/{case_id}", response_class=HTMLResponse)
def share_case(case_id: int, db: Session = Depends(get_db)):
    case = (
        db.query(MissingCase)
        .filter(MissingCase.id == case_id, MissingCase.status == "publicado")
        .first()
    )

    if not case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")

    title = f"{case.full_name} | Rede Alerta"

    description_parts = [
        f"{case.age} anos" if case.age is not None else None,
        f"{case.city}/{case.state}" if case.city and case.state else None,
        f"Desaparecido(a) em {case.missing_date}" if case.missing_date else None,
    ]
    base_description = " • ".join([part for part in description_parts if part])

    if case.case_description:
        description = f"{base_description}. {case.case_description[:120]}".strip()
    else:
        description = base_description or "Ajude a compartilhar este caso no Rede Alerta."

    image = resolve_image_url(case.photo_url)

    public_url = f"{FRONTEND_URL}/caso/{case.id}"
    redirect_url = public_url

    html_content = build_share_html(
        title=title,
        description=description,
        image=image,
        public_url=public_url,
        redirect_url=redirect_url,
        og_type="website",
    )

    return HTMLResponse(content=html_content, status_code=200)