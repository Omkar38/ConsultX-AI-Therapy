from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence

from .analysis import RiskAdapter, RiskClassifier, SentimentAnalyzer
from .models import (
    BufferSnapshot,
    MessageRecord,
    RiskAssessment,
    RiskTier,
    SenderRole,
    SentimentBand,
    SentimentResult,
    SessionMetrics,
    SessionRecord,
    SessionStatus,
    SessionSummary,
    utc_now,
)
from .storage import SessionStorage


class SessionError(Exception):
    """Base error for session-related failures."""


class SessionNotFound(SessionError):
    """Raised when a session id cannot be located."""


class SessionClosed(SessionError):
    """Raised when a write is attempted on an ended session."""


RISK_SEVERITY = {
    RiskTier.OK: 0,
    RiskTier.CAUTION: 1,
    RiskTier.HIGH: 2,
    RiskTier.CRISIS: 3,
}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _sentiment_band_from_score(score: float) -> SentimentBand:
    if score > 0.1:
        return SentimentBand.POSITIVE
    if score < -0.1:
        return SentimentBand.NEGATIVE
    return SentimentBand.NEUTRAL


@dataclass
class MessageAppendResult:
    message: MessageRecord
    risk: RiskAssessment
    buffer: BufferSnapshot
    metrics: SessionMetrics
    assistant_message: MessageRecord | None = None
    rag_result: Dict[str, Any] | None = None


class SessionTracker:
    """Core orchestration layer for session tracking and analytics."""

    def __init__(
        self,
        storage: Optional[SessionStorage] = None,
        *,
        buffer_size: int = 20,
        sentiment_analyzer: Optional[SentimentAnalyzer] = None,
        risk_classifier: Optional[RiskClassifier] = None,
        rag_runner: Optional[Callable[..., Dict[str, Any]]] = None,
        enable_rag: Optional[bool] = None,
        rag_auto_reply: Optional[bool] = None,
        rag_country_code: Optional[str] = None,
        rag_model: Optional[str] = None,
        rag_k: Optional[int] = None,
        rag_guardrails: Optional[bool] = None,
    ) -> None:
        self.storage = storage or SessionStorage()
        self.buffer_size = buffer_size
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()
        self.risk_classifier = risk_classifier or RiskClassifier()
        self.rag_enabled = enable_rag if enable_rag is not None else _env_flag("CONSULTX_ENABLE_RAG", True)
        self.rag_auto_reply = rag_auto_reply if rag_auto_reply is not None else _env_flag("CONSULTX_RAG_AUTOREPLY", True)
        self.rag_country_code = rag_country_code or os.environ.get("CONSULTX_RAG_COUNTRY", "US")
        self.rag_model = rag_model or os.environ.get("CONSULTX_RAG_MODEL", "gemini-2.0-flash")
        if rag_k is not None:
            self.rag_k = rag_k
        else:
            try:
                self.rag_k = int(os.environ.get("CONSULTX_RAG_K", "2"))
            except ValueError:
                self.rag_k = 2
        self.rag_guardrails = rag_guardrails if rag_guardrails is not None else _env_flag("CONSULTX_RAG_GUARDRAILS", True)
        self._rag_runner = rag_runner
        self._rag_error: str | None = None

    # Session lifecycle ---------------------------------------------------

    def create_session(self, user_id: str, metadata: Optional[dict] = None) -> SessionRecord:
        session = SessionRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            status=SessionStatus.ACTIVE,
            created_at=utc_now(),
            updated_at=utc_now(),
            active_risk_tier=RiskTier.OK,
            metadata=metadata or {},
        )
        self.storage.create_session(session)
        self.storage.save_buffer(BufferSnapshot(session_id=session.id, messages=[], capacity=self.buffer_size))
        return session

    def get_session(self, session_id: str) -> SessionRecord:
        session = self.storage.get_session(session_id)
        if not session:
            raise SessionNotFound(f"Session '{session_id}' not found.")
        return session

    def list_sessions(
        self,
        *,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
    ) -> List[SessionRecord]:
        return self.storage.list_sessions(user_id=user_id, status=status)

    def end_session(self, session_id: str) -> SessionSummary:
        session = self.get_session(session_id)
        if session.status == SessionStatus.ENDED:
            return self.get_summary(session_id)

        metrics, flagged = self._recalculate_metrics(session_id)
        self.storage.update_session(
            session_id,
            status=SessionStatus.ENDED,
            active_risk_tier=metrics.max_risk_tier,
        )
        session = self.get_session(session_id)
        summary = self._build_summary(session, metrics, flagged_keywords=flagged)
        return summary

    # Message handling ----------------------------------------------------

    def append_message(
        self,
        session_id: str,
        *,
        sender: SenderRole,
        content: str,
        use_rag: Optional[bool] = None,
        auto_reply: Optional[bool] = None,
    ) -> MessageAppendResult:
        session = self.get_session(session_id)
        if session.status != SessionStatus.ACTIVE:
            raise SessionClosed(f"Session '{session_id}' is not active.")

        rag_requested = use_rag if use_rag is not None else self.rag_enabled
        auto_respond = auto_reply if auto_reply is not None else self.rag_auto_reply

        sentiment = self.sentiment_analyzer.score(content)
        recent_messages = self.storage.recent_messages(session_id, self.buffer_size)
        recent_tiers = [m.risk_tier for m in recent_messages]
        assessment = self.risk_classifier.assess(content, sentiment, recent_tiers)

        rag_result: Dict[str, Any] | None = None
        rag_assessment: RiskAssessment | None = None
        if rag_requested and sender == SenderRole.USER:
            rag_result = self._run_rag_turn(
                session_id,
                content,
                history_summary=self._build_history_summary(session_id),
                transcript_block=self._build_transcript_block(session_id),
            )
            rag_assessment = self._map_rag_risk(rag_result.get("risk") if rag_result else None, sentiment)
            if rag_assessment:
                assessment = self._merge_assessments(assessment, rag_assessment)
            elif rag_result and rag_result.get("error"):
                assessment.notes.append(f"RAG unavailable: {rag_result['error']}")

        if rag_result:
            guardrail_action = rag_result.get("guardrail_action")
            guardrail_notes = rag_result.get("guardrail_notes") or []
            if guardrail_action:
                assessment.notes.append(f"Guardrail action: {guardrail_action}")
            for note in guardrail_notes:
                assessment.notes.append(str(note))

        message = MessageRecord(
            id=None,
            session_id=session_id,
            sender=sender,
            content=content,
            sentiment_score=sentiment.score,
            risk_tier=assessment.tier,
            risk_score=assessment.score,
            flagged_keywords=assessment.flagged_keywords,
            created_at=utc_now(),
        )
        saved_message = self.storage.insert_message(message)
        self.storage.update_session(session_id, active_risk_tier=assessment.tier)
        buffer = self._update_buffer(session_id)
        metrics, _ = self._recalculate_metrics(session_id)

        assistant_message: MessageRecord | None = None
        if rag_result and rag_result.get("reply") and auto_respond and sender == SenderRole.USER:
            assistant_message = self._append_assistant_reply(session_id, rag_result["reply"])
            buffer = self._update_buffer(session_id)
            metrics, _ = self._recalculate_metrics(session_id)

        return MessageAppendResult(
            message=saved_message,
            risk=assessment,
            buffer=buffer,
            metrics=metrics,
            assistant_message=assistant_message,
            rag_result=self._build_rag_payload(rag_result) if rag_requested else None,
        )

    def get_messages(self, session_id: str) -> List[MessageRecord]:
        self.get_session(session_id)  # ensure exists
        return self.storage.list_messages(session_id)

    def get_buffer(self, session_id: str) -> BufferSnapshot:
        buffer = self.storage.load_buffer(session_id)
        if buffer:
            return buffer
        self.get_session(session_id)  # raises if missing
        recent = self.storage.recent_messages(session_id, self.buffer_size)
        snapshot = BufferSnapshot(session_id=session_id, messages=recent, capacity=self.buffer_size)
        self.storage.save_buffer(snapshot)
        return snapshot

    # RAG integration ----------------------------------------------------

    def _load_rag_runner(self) -> Optional[Callable[..., Dict[str, Any]]]:
        if self._rag_runner:
            return self._rag_runner
        try:
            from .core_adapter import run_therapy_turn
        except Exception as exc:  # pragma: no cover - optional dependency path
            self._rag_error = str(exc)
            return None
        self._rag_runner = run_therapy_turn
        return self._rag_runner

    def _run_rag_turn(
        self,
        session_id: str,
        content: str,
        *,
        history_summary: str = "",
        transcript_block: str = "",
    ) -> Dict[str, Any]:
        runner = self._load_rag_runner()
        if not runner:
            return {"error": self._rag_error or "RAG runner unavailable"}
        try:
            result = runner(
                user_message=content,
                country_code=self.rag_country_code,
                history_summary=history_summary,
                transcript_block=transcript_block,
                k=self.rag_k,
                model=self.rag_model,
                session_id=session_id,
                use_guardrails=self.rag_guardrails,
            )
            self._rag_error = None
            return result
        except Exception as exc:  # pragma: no cover - surfaced to caller
            self._rag_error = str(exc)
            return {"error": str(exc)}

    def _build_history_summary(self, session_id: str) -> str:
        metrics = self.storage.get_metrics(session_id)
        if not metrics:
            return ""
        parts = [
            f"messages={metrics.message_count}",
            f"max_risk={metrics.max_risk_tier.value}",
        ]
        if metrics.trend_notes:
            parts.append("notes=" + "; ".join(metrics.trend_notes))
        return " | ".join(parts)

    def _build_transcript_block(self, session_id: str, max_pairs: int = 5) -> str:
        recent = self.storage.recent_messages(session_id, max_pairs * 2)
        lines: List[str] = []
        for message in recent[-max_pairs * 2 :]:
            if message.sender == SenderRole.USER:
                prefix = "User"
            elif message.sender == SenderRole.ASSISTANT:
                prefix = "Therapist"
            else:
                prefix = "System"
            lines.append(f"{prefix}: {message.content}")
        return "\n".join(lines)

    def _map_rag_risk(self, risk: Optional[Dict[str, Any]], sentiment: SentimentResult) -> Optional[RiskAssessment]:
        if not risk:
            return None
        try:
            tier = RiskTier(str(risk.get("tier", "ok")).lower())
        except ValueError:
            tier = RiskTier.OK
        raw_score = risk.get("score")
        try:
            score = float(raw_score) if raw_score is not None else 0.0
        except (TypeError, ValueError):
            score = max(0.0, -sentiment.score)
        flagged_keywords: List[str] = []
        for dim in risk.get("dimensions") or []:
            if isinstance(dim, str):
                flagged_keywords.append(dim)
        notes: List[str] = []
        if risk.get("emotion"):
            notes.append(f"Emotion: {risk['emotion']}")
        if risk.get("confidence") is not None:
            notes.append(f"Confidence: {risk['confidence']}")
        return RiskAssessment(
            tier=tier,
            score=round(score, 3),
            flagged_keywords=sorted(set(flagged_keywords)),
            notes=notes,
        )

    def _merge_assessments(self, primary: RiskAssessment, secondary: Optional[RiskAssessment]) -> RiskAssessment:
        if not secondary:
            return primary
        tier = primary.tier
        if RISK_SEVERITY[secondary.tier] > RISK_SEVERITY[tier]:
            tier = secondary.tier
        score = max(primary.score, secondary.score)
        flagged = sorted(set(primary.flagged_keywords + secondary.flagged_keywords))
        notes = list(primary.notes)
        for note in secondary.notes:
            if note not in notes:
                notes.append(note)
        return RiskAssessment(
            tier=tier,
            score=round(score, 3),
            flagged_keywords=flagged,
            notes=notes,
        )

    def _append_assistant_reply(self, session_id: str, reply: str) -> MessageRecord:
        sentiment = self.sentiment_analyzer.score(reply)
        recent_messages = self.storage.recent_messages(session_id, self.buffer_size)
        recent_tiers = [m.risk_tier for m in recent_messages]
        assessment = self.risk_classifier.assess(reply, sentiment, recent_tiers)
        message = MessageRecord(
            id=None,
            session_id=session_id,
            sender=SenderRole.ASSISTANT,
            content=reply,
            sentiment_score=sentiment.score,
            risk_tier=assessment.tier,
            risk_score=assessment.score,
            flagged_keywords=assessment.flagged_keywords,
            created_at=utc_now(),
        )
        saved = self.storage.insert_message(message)
        self.storage.update_session(session_id)  # bump updated_at without lowering risk
        return saved

    def _build_rag_payload(self, rag_result: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if rag_result is None:
            if self._rag_error:
                return {"error": self._rag_error}
            return None
        payload = {
            "reply": rag_result.get("reply"),
            "reply_raw": rag_result.get("reply_raw"),
            "risk": rag_result.get("risk"),
            "guardrail_action": rag_result.get("guardrail_action"),
            "guardrail_notes": rag_result.get("guardrail_notes"),
            "docs": rag_result.get("docs"),
            "prompt": rag_result.get("prompt"),
        }
        if rag_result.get("error"):
            payload["error"] = rag_result["error"]
        return payload

    # Summaries -----------------------------------------------------------

    def get_summary(self, session_id: str) -> SessionSummary:
        session = self.get_session(session_id)
        metrics = self.storage.get_metrics(session_id)
        flagged = self._collect_flagged_keywords(session_id)
        if not metrics:
            metrics, flagged = self._recalculate_metrics(session_id)
        return self._build_summary(session, metrics, flagged_keywords=flagged)

    # Internal helpers ----------------------------------------------------

    def _update_buffer(self, session_id: str) -> BufferSnapshot:
        recent = self.storage.recent_messages(session_id, self.buffer_size)
        snapshot = BufferSnapshot(session_id=session_id, messages=recent, capacity=self.buffer_size)
        self.storage.save_buffer(snapshot)
        return snapshot

    def _collect_flagged_keywords(self, session_id: str) -> List[str]:
        messages = self.storage.list_messages(session_id)
        keywords = set()
        for message in messages:
            keywords.update(message.flagged_keywords)
        return sorted(keywords)

    def _recalculate_metrics(self, session_id: str) -> tuple[SessionMetrics, List[str]]:
        messages = self.storage.list_messages(session_id)
        message_count = len(messages)
        user_turns = sum(1 for m in messages if m.sender == SenderRole.USER)
        assistant_turns = sum(1 for m in messages if m.sender == SenderRole.ASSISTANT)
        avg_sentiment = round(sum(m.sentiment_score for m in messages) / message_count, 3) if message_count else 0.0

        tier_counts = {tier.value: 0 for tier in RiskTier}
        band_counts = {band.value: 0 for band in SentimentBand}
        flagged_keywords = set()
        recent_risk = []
        for message in messages:
            tier_counts[message.risk_tier.value] += 1
            band = _sentiment_band_from_score(message.sentiment_score)
            band_counts[band.value] += 1
            flagged_keywords.update(message.flagged_keywords)
            recent_risk.append(message.risk_tier)

        max_risk_tier = RiskTier.OK
        for tier in RiskTier:
            if tier_counts[tier.value] and RISK_SEVERITY[tier] >= RISK_SEVERITY[max_risk_tier]:
                max_risk_tier = tier

        trend_notes: List[str] = []
        if recent_risk:
            last_three = recent_risk[-3:]
            if all(tier in {RiskTier.CAUTION, RiskTier.HIGH, RiskTier.CRISIS} for tier in last_three):
                trend_notes.append("Sustained elevated risk across last three turns.")
            if len(recent_risk) >= 2 and RISK_SEVERITY[recent_risk[-1]] > RISK_SEVERITY[recent_risk[-2]]:
                trend_notes.append("Risk climbing on most recent turn.")
            if avg_sentiment < -0.3:
                trend_notes.append("Overall negative sentiment.")

        suggested_resources = self.risk_classifier.suggest_resources(
            flagged_keywords,
            max_risk_tier,
        )

        metrics = SessionMetrics(
            session_id=session_id,
            message_count=message_count,
            user_turns=user_turns,
            assistant_turns=assistant_turns,
            avg_sentiment=avg_sentiment,
            max_risk_tier=max_risk_tier,
            tier_counts=tier_counts,
            band_counts=band_counts,
            trend_notes=trend_notes,
            suggested_resources=suggested_resources,
        )
        self.storage.upsert_metrics(metrics)
        return metrics, sorted(flagged_keywords)

    def _build_summary(
        self,
        session: SessionRecord,
        metrics: SessionMetrics,
        *,
        flagged_keywords: List[str],
    ) -> SessionSummary:
        duration_seconds = int(max(0.0, (session.updated_at - session.created_at).total_seconds()))
        notes = list(metrics.trend_notes)
        if session.status == SessionStatus.ENDED:
            notes.append("Session marked as ended.")
        return SessionSummary(
            session=session,
            metrics=metrics,
            duration_seconds=duration_seconds,
            flagged_keywords=flagged_keywords,
            notes=notes,
        )

    def register_risk_adapter(self, adapter: RiskAdapter) -> None:
        """Expose risk classifier adapter registration for external integrations."""
        self.risk_classifier.add_adapter(adapter)
