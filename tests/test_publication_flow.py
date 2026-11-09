import unittest
import os
from datetime import datetime
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Tests must not construct the production Postgres engine during module import.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.database import Base
from app.models import MissingCase, SocialPublication
from app.moderation import triage_case
from app.privacy import public_case_payload
from app.social import publish_instagram_once
from app.routes.share import share_case


def case_data(**overrides):
    values = {
        "id": None,
        "full_name": "Maria Aparecida Silva",
        "age": 22,
        "city": "Cuiabá",
        "state": "MT",
        "missing_date": "2026-10-12",
        "last_seen_clothes": "Camiseta azul e calça jeans.",
        "physical_traits": "Cabelos castanhos.",
        "case_description": "Foi vista pela última vez perto da rodoviária municipal.",
        "police_report_number": "BO-123456",
        "contact_name": "João da Silva",
        "contact_phone": "(65) 99999-0000",
        "photo_url": "https://cdn.example.test/maria.jpg",
        "status": "pending",
        "created_at": datetime.utcnow(),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class TriageTests(unittest.TestCase):
    def test_complete_consistent_case_is_eligible(self):
        result = triage_case(case_data())
        self.assertTrue(result.eligible)
        self.assertEqual(result.reasons, [])

    def test_incomplete_and_suspicious_case_is_kept_for_review(self):
        result = triage_case(case_data(full_name="Maria", case_description="teste http://spam.example"))
        self.assertFalse(result.eligible)
        self.assertIn("nome completo ausente ou incompleto", result.reasons)
        self.assertIn("conteúdo potencialmente suspeito", result.reasons)

    def test_duplicate_case_is_kept_for_review(self):
        existing = case_data(id=5, status="published")
        result = triage_case(case_data(id=6), [existing])
        self.assertFalse(result.eligible)
        self.assertIn("possível duplicidade de cadastro", result.reasons)


class PrivacyTests(unittest.TestCase):
    def test_public_payload_never_exposes_private_fields(self):
        case = case_data(
            case_description="Responsável João da Silva; ligue para (65) 99999-0000. BO-123456"
        )
        payload = public_case_payload(case)
        self.assertNotIn("contact_name", payload)
        self.assertNotIn("contact_phone", payload)
        self.assertNotIn("police_report_number", payload)
        self.assertNotIn("João da Silva", payload["case_description"])
        self.assertNotIn("BO-123456", payload["case_description"])

    def test_share_page_uses_published_status_and_private_safe_metadata(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        db = sessionmaker(bind=engine)()
        try:
            case = MissingCase(
                full_name="Maria Aparecida Silva", age=22, city="Cuiabá", state="MT",
                missing_date="2026-10-12", police_report_number="BO-123456",
                contact_name="João da Silva", contact_phone="65999990000",
                case_description="João da Silva informou BO-123456 no cadastro.",
                status="published",
            )
            db.add(case)
            db.commit()
            response = share_case(case.id, db)
            self.assertEqual(response.status_code, 200)
            self.assertIn('property="og:url"', response.body.decode())
            self.assertNotIn("João da Silva", response.body.decode())
            self.assertNotIn("BO-123456", response.body.decode())
        finally:
            db.close()
            engine.dispose()


class SocialIdempotencyTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.case = MissingCase(
            full_name="Maria Aparecida Silva", age=22, city="Cuiabá", state="MT",
            missing_date="2026-10-12", police_report_number="BO-123456",
            contact_name="João da Silva", contact_phone="65999990000", status="published",
        )
        self.db.add(self.case)
        self.db.commit()
        self.db.refresh(self.case)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_successful_publication_is_not_sent_twice(self):
        calls = []

        def publish_callback(case):
            calls.append(case.id)
            return {"publish_result": {"id": "remote-42"}}

        first = publish_instagram_once(self.db, self.case, publish_callback)
        second = publish_instagram_once(self.db, self.case, publish_callback)

        self.assertEqual(first.status, "published")
        self.assertEqual(second.status, "published")
        self.assertEqual(calls, [self.case.id])
        self.assertEqual(self.db.query(SocialPublication).count(), 1)

    def test_ambiguous_failure_is_not_retried_blindly(self):
        calls = []

        def publish_callback(case):
            calls.append(case.id)
            raise RuntimeError("conexão encerrada após envio")

        first = publish_instagram_once(self.db, self.case, publish_callback)
        second = publish_instagram_once(self.db, self.case, publish_callback)

        self.assertEqual(first.status, "unknown")
        self.assertEqual(second.status, "unknown")
        self.assertEqual(calls, [self.case.id])

