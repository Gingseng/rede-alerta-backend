"""Safe, idempotent social-publication orchestration."""

from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy.orm import Session

from . import models


MAX_SOCIAL_ATTEMPTS = int(os.getenv("SOCIAL_MAX_ATTEMPTS", "3"))


def platform_configuration() -> dict[str, dict[str, object]]:
    # Keep persistence and idempotency usable even in test environments where
    # optional image/social clients are intentionally not installed.
    from .instagram_service import is_instagram_configured

    backend_url = bool(os.getenv("BACKEND_PUBLIC_URL", "").strip())
    instagram_ready = bool(is_instagram_configured() and backend_url)
    facebook_token = bool(os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip())
    facebook_page = bool(os.getenv("FACEBOOK_PAGE_ID", "").strip())
    facebook_ready = bool(facebook_token and facebook_page and backend_url)
    return {
        "instagram": {
            "configured": instagram_ready,
            "ready": instagram_ready,
            "message": "Instagram pronto para publicação automática."
            if instagram_ready
            else "Instagram pendente: configure INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID e BACKEND_PUBLIC_URL.",
        },
        "facebook": {
            "configured": facebook_ready,
            "ready": facebook_ready,
            "message": "Facebook pronto para publicação automática."
            if facebook_ready
            else "Facebook pendente: configure FACEBOOK_PAGE_ACCESS_TOKEN, FACEBOOK_PAGE_ID e BACKEND_PUBLIC_URL.",
        },
    }


def get_or_create_publication(db: Session, case_id: int, platform: str):
    publication = (
        db.query(models.SocialPublication)
        .filter_by(case_id=case_id, platform=platform)
        .first()
    )
    if publication:
        return publication
    publication = models.SocialPublication(
        case_id=case_id, platform=platform, status="pending", attempt_count=0
    )
    db.add(publication)
    db.commit()
    db.refresh(publication)
    return publication


def mark_configuration_pending(db: Session, case_id: int, platform: str, message: str):
    publication = get_or_create_publication(db, case_id, platform)
    if publication.status != "published":
        publication.status = "configuration_pending"
        publication.last_error = message
        db.commit()
        db.refresh(publication)
    return publication


def publish_social_once(db: Session, case, platform: str, publish_callback):
    """Attempts exactly once per stored publication record.

    The record is committed as ``publishing`` before the external call. Any
    ambiguous network result becomes ``unknown`` and is deliberately not retried,
    preventing a second post after a platform may already have accepted the first.
    """
    publication = get_or_create_publication(db, case.id, platform)
    if publication.status in {"published", "publishing", "unknown"}:
        return publication
    if publication.attempt_count >= MAX_SOCIAL_ATTEMPTS:
        publication.status = "failed"
        publication.last_error = "Limite de tentativas atingido."
        db.commit()
        return publication

    publication.status = "publishing"
    publication.attempt_count += 1
    publication.last_error = None
    db.commit()

    try:
        result = publish_callback(case)
        publication.status = "published"
        publication.remote_post_id = str(
            (result.get("publish_result") or {}).get("id") or ""
        ) or None
        publication.published_at = datetime.utcnow()
    except Exception as exc:  # External call may have reached the provider.
        publication.status = "unknown"
        publication.last_error = str(exc)[:1000]
    db.commit()
    db.refresh(publication)
    return publication


def publish_instagram_once(db: Session, case, publish_callback):
    """Compatibility wrapper for the current Instagram admin endpoint."""
    return publish_social_once(db, case, "instagram", publish_callback)
