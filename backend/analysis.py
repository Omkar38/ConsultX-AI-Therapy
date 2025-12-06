from __future__ import annotations

import re
from typing import Callable, Iterable, List, Optional, Sequence

from .models import (
    RiskAssessment,
    RiskTier,
    SentimentBand,
    SentimentResult,
)


_WORD_RE = re.compile(r"[a-zA-Z']+")

_RISK_SEVERITY = {
    RiskTier.OK: 0,
    RiskTier.CAUTION: 1,
    RiskTier.HIGH: 2,
    RiskTier.CRISIS: 3,
}

RiskAdapter = Callable[[str, SentimentResult], Optional[RiskAssessment]]


class SentimentAnalyzer:
    """Lexicon-based sentiment analyser that avoids external dependencies."""

    POSITIVE_WORDS = {
        "calm",
        "hope",
        "relief",
        "grateful",
        "progress",
        "better",
        "supported",
        "proud",
        "strong",
        "encouraged",
        "improving",
        "relaxed",
    }
    NEGATIVE_WORDS = {
        "sad",
        "angry",
        "upset",
        "anxious",
        "stressed",
        "scared",
        "lonely",
        "hopeless",
        "worthless",
        "tired",
        "empty",
        "numb",
        "depressed",
        "afraid",
        "ashamed",
        "guilty",
        "fail",
        "failure",
        "broken",
        "hurt",
    }
    NEGATIONS = {
        "not",
        "never",
        "no",
        "hardly",
        "barely",
    }

    def score(self, text: str) -> SentimentResult:
        tokens = [token.lower() for token in _WORD_RE.findall(text)]
        matched_tokens: List[str] = []
        score = 0
        total = 0

        for idx, token in enumerate(tokens):
            if token in self.POSITIVE_WORDS:
                modifier = -1 if idx > 0 and tokens[idx - 1] in self.NEGATIONS else 1
                score += modifier
                total += 1
                matched_tokens.append(token)
            elif token in self.NEGATIVE_WORDS:
                modifier = -1 if idx > 0 and tokens[idx - 1] in self.NEGATIONS else 1
                score -= modifier
                total += 1
                matched_tokens.append(token)

        normalized = score / total if total else 0.0
        if normalized > 0.1:
            band = SentimentBand.POSITIVE
        elif normalized < -0.1:
            band = SentimentBand.NEGATIVE
        else:
            band = SentimentBand.NEUTRAL

        return SentimentResult(score=round(normalized, 3), band=band, tokens=matched_tokens)


class RiskClassifier:
    """Keyword-driven risk evaluator inspired by proposal safety requirements."""

    def __init__(self, adapters: Optional[Sequence[RiskAdapter]] = None) -> None:
        self.adapters: List[RiskAdapter] = list(adapters or [])

    CRISIS_PHRASES = {
        "kill myself",
        "end my life",
        "suicide",
        "take my life",
        "hurt myself",
        "want to die",
        "ending it all",
    }
    HIGH_KEYWORDS = {
        "cut",
        "self-harm",
        "jump",
        "overdose",
        "plan",
        "no reason",
        "can't go on",
        "die",
    }
    CAUTION_KEYWORDS = {
        "numb",
        "worthless",
        "hopeless",
        "empty",
        "lost",
        "alone",
        "tired",
        "fail",
        "failure",
        "break",
        "breaking",
        "drowning",
        "spiral",
        "panic",
        "overwhelmed",
        "burnout",
        "grief",
        "insomnia",
    }

    RESOURCE_MAP = {
        "suicide": {
            "type": "hotline",
            "label": "988 Suicide & Crisis Lifeline",
            "link": "tel:988",
        },
        "hurt myself": {
            "type": "hotline",
            "label": "Crisis Text Line",
            "link": "sms:741741",
        },
        "hopeless": {
            "type": "article",
            "label": "Grounding exercise: 5-4-3-2-1 method",
            "link": "https://www.healthline.com/health/grounding-techniques",
        },
        "lonely": {
            "type": "resource",
            "label": "Mental Health America peer support",
            "link": "https://mhanational.org/peers",
        },
        "anxious": {
            "type": "exercise",
            "label": "Box breathing technique",
            "link": "https://www.va.gov/WHOLEHEALTHLIBRARY/tools/box-breathing.asp",
        },
        "panic": {
            "type": "exercise",
            "label": "Panic attack grounding steps",
            "link": "https://www.verywellmind.com/stop-a-panic-attack-2584406",
        },
        "overwhelmed": {
            "type": "article",
            "label": "Guided journaling prompts for overwhelm",
            "link": "https://www.therapistaid.com/worksheets/coping-skills-anxiety.pdf",
        },
        "self-harm": {
            "type": "hotline",
            "label": "Self-Injury Outreach & Support",
            "link": "https://sioutreach.org/dont-hurt-yourself/",
        },
        "grief": {
            "type": "resource",
            "label": "Grief Share support groups",
            "link": "https://www.griefshare.org/findagroup",
        },
        "insomnia": {
            "type": "exercise",
            "label": "Sleep hygiene checklist",
            "link": "https://www.sleepfoundation.org/sleep-hygiene",
        },
        "burnout": {
            "type": "article",
            "label": "Burnout recovery micro-breaks",
            "link": "https://www.apa.org/topics/burnout/recover",
        },
    }

    def add_adapter(self, adapter: RiskAdapter) -> None:
        """Register an external risk adapter."""
        self.adapters.append(adapter)

    def assess(
        self,
        text: str,
        sentiment: SentimentResult,
        recent_tiers: Sequence[RiskTier] | None = None,
    ) -> RiskAssessment:
        recent_tiers = recent_tiers or []
        lowered = text.lower()
        flagged: List[str] = []
        notes: List[str] = []

        tier = RiskTier.OK
        score = 0.0

        crisis_hits = self._find_phrases(lowered, self.CRISIS_PHRASES)
        if crisis_hits:
            flagged.extend(crisis_hits)
            tier = RiskTier.CRISIS
            score = 1.0
            notes.append("Crisis phrase detected.")
        else:
            high_hits = self._find_keywords(lowered, self.HIGH_KEYWORDS)
            caution_hits = self._find_keywords(lowered, self.CAUTION_KEYWORDS)

            if high_hits:
                flagged.extend(high_hits)
                tier = RiskTier.HIGH
                score = max(score, 0.75)
                notes.append("High-risk language detected.")
            if caution_hits and tier != RiskTier.CRISIS:
                flagged.extend(caution_hits)
                if tier == RiskTier.OK:
                    tier = RiskTier.CAUTION
                    score = max(score, 0.4)
                notes.append("Cautionary language present.")

            if tier == RiskTier.OK:
                score = max(score, max(0.0, -sentiment.score))

            if tier == RiskTier.OK and sentiment.band == SentimentBand.NEGATIVE:
                tier = RiskTier.CAUTION
                score = max(score, min(0.4, abs(sentiment.score)))
                notes.append("Negative sentiment triggered caution tier.")

            if recent_tiers:
                if recent_tiers[-2:].count(RiskTier.HIGH) == 2 and tier != RiskTier.CRISIS:
                    tier = RiskTier.HIGH
                    score = max(score, 0.8)
                    notes.append("Repeated high risk in recent history.")
                if (
                    tier in {RiskTier.CAUTION, RiskTier.HIGH}
                    and recent_tiers
                    and recent_tiers[-1] in {RiskTier.CAUTION, RiskTier.HIGH}
                ):
                    score = max(score, 0.6)
                    notes.append("Risk trend escalating.")

        tier, score, adapter_flagged, adapter_notes = self._apply_adapters(text, sentiment, tier, score)
        flagged.extend(adapter_flagged)
        if adapter_notes:
            notes.extend(adapter_notes)

        unique_flagged = sorted(set(flagged))
        return RiskAssessment(tier=tier, score=round(score, 3), flagged_keywords=unique_flagged, notes=notes)

    @staticmethod
    def _find_phrases(text: str, phrases: Iterable[str]) -> List[str]:
        hits = []
        for phrase in phrases:
            if phrase in text:
                hits.append(phrase)
        return hits

    @staticmethod
    def _find_keywords(text: str, keywords: Iterable[str]) -> List[str]:
        hits: List[str] = []
        token_set = set(_WORD_RE.findall(text))
        for keyword in keywords:
            if " " in keyword:
                if keyword in text:
                    hits.append(keyword)
            else:
                if keyword in token_set:
                    hits.append(keyword)
        return hits

    def suggest_resources(self, keywords: Iterable[str], tier: RiskTier) -> List[dict]:
        suggestions: List[dict] = []
        for keyword in keywords:
            resource = self.RESOURCE_MAP.get(keyword)
            if resource:
                suggestions.append(resource)

        if tier in {RiskTier.HIGH, RiskTier.CRISIS} and not any(
            res for res in suggestions if res.get("type") == "hotline"
        ):
            suggestions.append(
                {
                    "type": "hotline",
                    "label": "988 Suicide & Crisis Lifeline",
                    "link": "tel:988",
                }
            )
        return suggestions

    def _apply_adapters(
        self,
        text: str,
        sentiment: SentimentResult,
        current_tier: RiskTier,
        current_score: float,
    ) -> tuple[RiskTier, float, List[str], List[str]]:
        flagged: List[str] = []
        tier = current_tier
        score = current_score
        notes: List[str] = []

        for adapter in self.adapters:
            try:
                result = adapter(text, sentiment)
            except Exception as exc:  # pragma: no cover - defensive logging
                notes.append(f"Adapter '{getattr(adapter, '__name__', repr(adapter))}' failed: {exc}")
                continue
            if not result:
                continue
            flagged.extend(result.flagged_keywords)
            if _RISK_SEVERITY[result.tier] > _RISK_SEVERITY[tier]:
                tier = result.tier
                notes.append(
                    f"Adapter '{getattr(adapter, '__name__', repr(adapter))}' escalated tier to {result.tier.value}."
                )
            score = max(score, result.score)
            if result.notes:
                notes.extend(result.notes)

        return tier, score, flagged, notes
