from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class RiskTier(str, Enum):
    OK = "ok"
    CAUTION = "caution"
    HIGH = "high"
    CRISIS = "crisis"


class SentimentBand(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"


class SenderRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class MessageRecord:
    session_id: str
    sender: SenderRole
    content: str
    sentiment_score: float
    risk_tier: RiskTier
    risk_score: float
    flagged_keywords: List[str]
    created_at: datetime
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, object]:
        data = asdict(self)
        data["sender"] = self.sender.value
        data["risk_tier"] = self.risk_tier.value
        data["created_at"] = self.created_at.isoformat()
        return data


@dataclass
class SessionRecord:
    id: str
    user_id: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    active_risk_tier: RiskTier
    metadata: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "active_risk_tier": self.active_risk_tier.value,
            "metadata": self.metadata,
        }
        return data


@dataclass
class SessionMetrics:
    session_id: str
    message_count: int
    user_turns: int
    assistant_turns: int
    avg_sentiment: float
    max_risk_tier: RiskTier
    tier_counts: Dict[str, int]
    band_counts: Dict[str, int]
    trend_notes: List[str]
    suggested_resources: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, object]:
        return {
            "session_id": self.session_id,
            "message_count": self.message_count,
            "user_turns": self.user_turns,
            "assistant_turns": self.assistant_turns,
            "avg_sentiment": self.avg_sentiment,
            "max_risk_tier": self.max_risk_tier.value,
            "tier_counts": self.tier_counts,
            "band_counts": self.band_counts,
            "trend_notes": self.trend_notes,
            "suggested_resources": self.suggested_resources,
        }


@dataclass
class SessionSummary:
    session: SessionRecord
    metrics: SessionMetrics
    duration_seconds: int
    flagged_keywords: List[str]
    notes: List[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "session": self.session.to_dict(),
            "metrics": self.metrics.to_dict(),
            "duration_seconds": self.duration_seconds,
            "flagged_keywords": self.flagged_keywords,
            "notes": self.notes,
        }


@dataclass
class BufferSnapshot:
    session_id: str
    messages: List[MessageRecord]
    capacity: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "session_id": self.session_id,
            "capacity": self.capacity,
            "messages": [msg.to_dict() for msg in self.messages],
        }


@dataclass
class RiskAssessment:
    tier: RiskTier
    score: float
    flagged_keywords: List[str]
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "tier": self.tier.value,
            "score": self.score,
            "flagged_keywords": self.flagged_keywords,
            "notes": self.notes,
        }


@dataclass
class SentimentResult:
    score: float
    band: SentimentBand
    tokens: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "score": self.score,
            "band": self.band.value,
            "tokens": self.tokens,
        }
