import os
import requests
from dotenv import load_dotenv

load_dotenv()

INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

GRAPH_API_BASE_URL = "https://graph.facebook.com/v23.0"


def is_instagram_configured():
    return bool(INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID)


def create_instagram_media_container(image_url: str, caption: str):
    if not is_instagram_configured():
        raise ValueError(
            "Instagram não configurado. Verifique INSTAGRAM_ACCESS_TOKEN e INSTAGRAM_ACCOUNT_ID."
        )

    url = f"{GRAPH_API_BASE_URL}/{INSTAGRAM_ACCOUNT_ID}/media"

    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    }

    response = requests.post(url, data=payload, timeout=30)

    if not response.ok:
        raise ValueError(
            f"Erro ao criar container no Instagram. "
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