"""Public case serialization with an explicit allow-list."""

from __future__ import annotations


PUBLIC_CASE_FIELDS = (
    "id", "full_name", "age", "city", "state", "missing_date",
    "last_seen_clothes", "physical_traits", "case_description", "photo_url",
    "status", "created_at",
)


def _strip_private_values(value: str | None, case) -> str | None:
    if value is None:
        return None
    cleaned = value
    for private_value in (
        getattr(case, "contact_name", None),
        getattr(case, "contact_phone", None),
        getattr(case, "police_report_number", None),
    ):
        if private_value:
            cleaned = cleaned.replace(str(private_value), "[dado privado removido]")
    return cleaned


def public_case_payload(case) -> dict:
    payload = {field: getattr(case, field) for field in PUBLIC_CASE_FIELDS}
    for field in ("last_seen_clothes", "physical_traits", "case_description"):
        payload[field] = _strip_private_values(payload[field], case)
    return payload
