import os
import uuid
from io import BytesIO

import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "").rstrip("/")

GRAPH_API_BASE_URL = os.getenv(
    "INSTAGRAM_GRAPH_API_BASE_URL",
    "https://graph.instagram.com/v23.0"
).rstrip("/")

INSTAGRAM_CACHE_DIR = "app/uploads/instagram_cache"
os.makedirs(INSTAGRAM_CACHE_DIR, exist_ok=True)


def is_instagram_configured():
    return bool(INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID)


def is_jpeg_url(image_url: str) -> bool:
    lower = image_url.lower().split("?")[0]
    return lower.endswith(".jpg") or lower.endswith(".jpeg")


def build_public_cached_jpeg_url(filename: str) -> str:
    if not BACKEND_PUBLIC_URL:
        raise ValueError(
            "BACKEND_PUBLIC_URL não configurado. Não foi possível montar a URL pública do JPEG."
        )

    return f"{BACKEND_PUBLIC_URL}/uploads/instagram_cache/{filename}"


def convert_image_url_to_public_jpeg(image_url: str) -> str:
    """
    Baixa a imagem pública, converte para JPEG e salva no backend
    para gerar uma URL pública válida para o Instagram.
    """
    if not image_url:
        raise ValueError("image_url não informada.")

    if is_jpeg_url(image_url):
        return image_url

    response = requests.get(image_url, timeout=30)
    if not response.ok:
        raise ValueError(
            f"Não foi possível baixar a imagem para conversão. "
            f"Status: {response.status_code}. "
            f"URL: {image_url}"
        )

    try:
        image = Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as e:
        raise ValueError(f"Falha ao abrir/interpretar a imagem para conversão: {e}")

    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(INSTAGRAM_CACHE_DIR, filename)

    try:
        image.save(filepath, format="JPEG", quality=95, optimize=True)
    except Exception as e:
        raise ValueError(f"Falha ao salvar JPEG convertido: {e}")

    return build_public_cached_jpeg_url(filename)


def create_instagram_media_container(image_url: str, caption: str):
    if not is_instagram_configured():
        raise ValueError(
            "Instagram não configurado. Verifique INSTAGRAM_ACCESS_TOKEN e INSTAGRAM_ACCOUNT_ID."
        )

    final_image_url = convert_image_url_to_public_jpeg(image_url)

    url = f"{GRAPH_API_BASE_URL}/{INSTAGRAM_ACCOUNT_ID}/media"

    payload = {
        "image_url": final_image_url,
        "caption": caption,
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    }

    response = requests.post(url, data=payload, timeout=30)

    if not response.ok:
        raise ValueError(
            f"Erro ao criar container no Instagram. "
            f"URL: {url}. "
            f"Image URL final: {final_image_url}. "
            f"Status: {response.status_code}. "
            f"Resposta: {response.text}"
        )

    return response.json()


def publish_instagram_media(creation_id: str):
    if not is_instagram_configured():
        raise ValueError(
            "Instagram não configurado. Verifique INSTAGRAM_ACCESS_TOKEN e INSTAGRAM_ACCOUNT_ID."
        )

    url = f"{GRAPH_API_BASE_URL}/{INSTAGRAM_ACCOUNT_ID}/media_publish"

    payload = {
        "creation_id": creation_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    }

    response = requests.post(url, data=payload, timeout=30)

    if not response.ok:
        raise ValueError(
            f"Erro ao publicar mídia no Instagram. "
            f"URL: {url}. "
            f"Status: {response.status_code}. "
            f"Resposta: {response.text}"
        )

    return response.json()


def publish_image_to_instagram(image_url: str, caption: str):
    container = create_instagram_media_container(image_url, caption)

    creation_id = container.get("id")
    if not creation_id:
        raise ValueError(
            f"Não foi possível obter o creation_id. Resposta: {container}"
        )

    publish_result = publish_instagram_media(creation_id)

    return {
        "container": container,
        "publish_result": publish_result,
    }