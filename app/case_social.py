"""Platform-specific public payloads. Private case fields are never included."""

from __future__ import annotations

import os
from typing import Optional

import requests

from .instagram_service import is_instagram_configured, publish_image_to_instagram
from .privacy import public_case_payload


def build_case_caption(case) -> str:
    public_case = public_case_payload(case)
    return f"""🚨 PESSOA DESAPARECIDA

{public_case['full_name']}, {public_case['age']} anos.
Última informação em {public_case['city']}/{public_case['state']} no dia {public_case['missing_date']}.

{public_case['case_description'] or "Qualquer informação pode ser essencial para ajudar neste caso."}

Compartilhe esta publicação para ampliar o alcance.

#RedeAlerta #Desaparecidos #AjudeACompartilhar #CadaMinutoConta"""


def build_public_image_url(photo_url: Optional[str]) -> Optional[str]:
    if not photo_url:
        return None
    if photo_url.startswith(("http://", "https://")):
        return photo_url
    backend_url = os.getenv("BACKEND_PUBLIC_URL", "").rstrip("/")
    if not backend_url:
        return None
    return f"{backend_url}/{photo_url.lstrip('/')}"


def publish_case_to_instagram(case):
    if not is_instagram_configured():
        raise ValueError("Instagram não configurado.")
    image_url = build_public_image_url(case.photo_url)
    if not image_url:
        raise ValueError("Imagem sem URL pública válida.")
    return publish_image_to_instagram(image_url=image_url, caption=build_case_caption(case))


def is_facebook_configured() -> bool:
    return bool(
        os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
        and os.getenv("FACEBOOK_PAGE_ID", "").strip()
    )


def publish_case_to_facebook(case):
    """Publish one image post to a configured Facebook Page Graph API endpoint."""
    if not is_facebook_configured():
        raise ValueError("Facebook não configurado.")
    image_url = build_public_image_url(case.photo_url)
    if not image_url:
        raise ValueError("Imagem sem URL pública válida.")

    base_url = os.getenv("FACEBOOK_GRAPH_API_BASE_URL", "https://graph.facebook.com/v23.0").rstrip("/")
    page_id = os.environ["FACEBOOK_PAGE_ID"].strip()
    response = requests.post(
        f"{base_url}/{page_id}/photos",
        data={
            "url": image_url,
            "caption": build_case_caption(case),
            "access_token": os.environ["FACEBOOK_PAGE_ACCESS_TOKEN"],
        },
        timeout=30,
    )
    if not response.ok:
        raise ValueError(f"Erro ao publicar no Facebook: status {response.status_code}.")
    return {"publish_result": response.json()}
