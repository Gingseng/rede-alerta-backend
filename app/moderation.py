"""Deterministic, conservative moderation rules for new case submissions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Iterable


BRAZILIAN_STATES = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT",
    "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO",
    "RR", "SC", "SP", "SE", "TO",
}
SUSPICIOUS_TERMS = ("teste", "test", "spam", "aposta", "bitcoin", "cripto", "http://", "https://", "www.")


@dataclass(frozen=True)
class TriageResult:
    eligible: bool
    reasons: list[str]


def normalize_case_fingerprint(full_name: str, missing_date: str, state: str) -> str:
    name = re.sub(r"\s+", " ", (full_name or "").strip().casefold())
    return f"{name}|{(missing_date or '').strip()}|{(state or '').strip().upper()}"


def triage_case(case, existing_cases: Iterable[object] = ()) -> TriageResult:
    """Returns safe-to-publish only when all public and private checks are clear.

    Flagged cases are intentionally kept in ``pending`` for an administrator; this
    function never rejects a report automatically.
    """
    reasons: list[str] = []
    full_name = (getattr(case, "full_name", "") or "").strip()
    city = (getattr(case, "city", "") or "").strip()
    state = (getattr(case, "state", "") or "").strip().upper()
    description = (getattr(case, "case_description", "") or "").strip()
    contact_name = (getattr(case, "contact_name", "") or "").strip()
    report_number = (getattr(case, "police_report_number", "") or "").strip()
    phone_digits = re.sub(r"\D", "", getattr(case, "contact_phone", "") or "")

    if len(full_name.split()) < 2:
        reasons.append("nome completo ausente ou incompleto")
    if not city:
        reasons.append("cidade ausente")
    if state not in BRAZILIAN_STATES:
        reasons.append("UF inválida")
    if not contact_name or len(phone_digits) < 10:
        reasons.append("dados de contato incompletos")
    if not report_number:
        reasons.append("número do boletim de ocorrência ausente")
    if not getattr(case, "photo_url", None):
        reasons.append("foto ausente para identificação e divulgação")
    if len(description) < 20:
        reasons.append("descrição insuficiente para divulgação pública")

    try:
        age = int(getattr(case, "age", 0))
        if not 0 < age < 130:
            reasons.append("idade inválida")
    except (TypeError, ValueError):
        reasons.append("idade inválida")

    missing_date = (getattr(case, "missing_date", "") or "").strip()
    try:
        parsed_date = date.fromisoformat(missing_date)
        if parsed_date > date.today():
            reasons.append("data de desaparecimento futura")
    except ValueError:
        reasons.append("data de desaparecimento inválida")

    public_text = " ".join((full_name, city, description)).casefold()
    if any(term in public_text for term in SUSPICIOUS_TERMS):
        reasons.append("conteúdo potencialmente suspeito")
    if re.search(r"(.)\1{7,}", public_text):
        reasons.append("conteúdo potencialmente suspeito")

    fingerprint = normalize_case_fingerprint(full_name, missing_date, state)
    for other in existing_cases:
        if getattr(other, "id", None) == getattr(case, "id", None):
            continue
        if getattr(other, "status", None) == "rejected":
            continue
        other_fingerprint = normalize_case_fingerprint(
            getattr(other, "full_name", ""),
            getattr(other, "missing_date", ""),
            getattr(other, "state", ""),
        )
        if fingerprint == other_fingerprint:
            reasons.append("possível duplicidade de cadastro")
            break

    return TriageResult(eligible=not reasons, reasons=reasons)
