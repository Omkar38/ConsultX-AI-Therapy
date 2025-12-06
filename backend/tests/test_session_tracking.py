import os
import tempfile
import unittest

from backend.models import RiskAssessment, RiskTier, SenderRole, SessionStatus
from backend.session_tracking import SessionClosed, SessionTracker
from backend.storage import SessionStorage


class SessionTrackerTestCase(unittest.TestCase):
    def setUp(self):
        fd, path = tempfile.mkstemp(prefix="consultx-test-", suffix=".db")
        os.close(fd)
        self.db_path = path
        storage = SessionStorage(self.db_path)
        self.tracker = SessionTracker(storage=storage, buffer_size=3)

    def tearDown(self):
        try:
            os.remove(self.db_path)
        except FileNotFoundError:
            pass

    def test_create_session_defaults(self):
        session = self.tracker.create_session("user-1")
        self.assertEqual(session.user_id, "user-1")
        self.assertEqual(session.status, SessionStatus.ACTIVE)
        self.assertEqual(session.active_risk_tier, RiskTier.OK)

    def test_append_message_updates_risk(self):
        session = self.tracker.create_session("user-risk")
        result = self.tracker.append_message(
            session.id,
            sender=SenderRole.USER,
            content="I want to kill myself tonight.",
        )
        self.assertEqual(result.risk.tier, RiskTier.CRISIS)
        self.assertIn("kill myself", result.risk.flagged_keywords)
        updated = self.tracker.get_session(session.id)
        self.assertEqual(updated.active_risk_tier, RiskTier.CRISIS)

    def test_buffer_capacity_enforced(self):
        session = self.tracker.create_session("user-buffer")
        for idx in range(5):
            self.tracker.append_message(
                session.id,
                sender=SenderRole.USER,
                content=f"I feel sad {idx}",
            )
        buffer = self.tracker.get_buffer(session.id)
        self.assertEqual(len(buffer.messages), 3)
        self.assertTrue(buffer.messages[0].content.endswith("2"))
        self.assertTrue(buffer.messages[-1].content.endswith("4"))

    def test_summary_after_end_session(self):
        session = self.tracker.create_session("user-summary")
        self.tracker.append_message(
            session.id,
            sender=SenderRole.USER,
            content="I feel hopeless and tired.",
        )
        self.tracker.append_message(
            session.id,
            sender=SenderRole.ASSISTANT,
            content="I hear you. Let's focus on breathing.",
        )
        summary = self.tracker.end_session(session.id)
        self.assertEqual(summary.session.status, SessionStatus.ENDED)
        self.assertGreaterEqual(summary.metrics.message_count, 2)
        self.assertIn("hopeless", summary.flagged_keywords)
        self.assertTrue(any("Session marked as ended." in note for note in summary.notes))

    def test_external_adapter_escalation(self):
        session = self.tracker.create_session("user-adapter")

        def adapter(text, sentiment):
            if "code red" in text.lower():
                return RiskAssessment(
                    tier=RiskTier.HIGH,
                    score=0.92,
                    flagged_keywords=["code red"],
                    notes=["External provider escalated risk."],
                )
            return None

        self.tracker.register_risk_adapter(adapter)
        result = self.tracker.append_message(
            session.id,
            sender=SenderRole.USER,
            content="This is a code red situation.",
        )
        self.assertEqual(result.risk.tier, RiskTier.HIGH)
        self.assertIn("code red", result.risk.flagged_keywords)
        self.assertTrue(any("External provider" in note for note in result.risk.notes))

    def test_cannot_append_to_closed_session(self):
        session = self.tracker.create_session("user-closed")
        self.tracker.end_session(session.id)
        with self.assertRaises(SessionClosed):
            self.tracker.append_message(
                session.id,
                sender=SenderRole.USER,
                content="Are you there?",
            )


if __name__ == "__main__":
    unittest.main()
