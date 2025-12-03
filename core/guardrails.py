
# ============================================================
"""
Guardrails for ConsultX.

Responsibilities:
- Detect crisis intent in *user* text and short-circuit to scripted crisis reply.
- Scan the *assistant reply* for obviously unsafe content (self-harm, harm-others, clinical overreach).
- Light-touch normalize MI tone for OK / Caution tiers when the LLM is already good.
- Heavier MI scaffolding + safety footer only for High-tier (and Crisis override).
"""
# ============================================================


from __future__ import annotations

import random
import re
from typing import Any, Dict, Optional



# -----------------------------
# Hard blocks / phrasing cleanup
# -----------------------------
_BAD_PHRASES = [
    "you’re naming how tough this is",
    "you're naming how tough this is",
    "you are naming how tough this is",
]


def _strip_bad_phrases(text: str) -> str:
    t = text or ""
    for p in _BAD_PHRASES:
        t = re.sub(re.escape(p), "", t, flags=re.I)
    return re.sub(r"\s{2,}", " ", t).strip()


# -----------------------------
# Crisis detection (user text)
# -----------------------------
_SUICIDE_RX = re.compile(
    r"\b("
    r"kill myself|suicide|suicidal|"
    r"end my life|ending my life|end it all|ending it all|"
    r"want to die|just want to die|"
    r"no reason to live|better off dead|"
    r"i don['’]t want to live|"
    r"don['’]t see a future for (myself|me)|"
    r"take my own life|"
    r"i can't go on anymore|i cannot go on anymore|"
    r"i can't go on|i cannot go on"
    r")\b",
    re.I,
)


def _is_suicidal_text(user_text: str) -> bool:
    return bool(_SUICIDE_RX.search(user_text or ""))


# -----------------------------
# Country-aware hotlines
# -----------------------------
HOTLINES = {
    "US": {
        "emergency": "911",
        "crisis": "988 (Suicide & Crisis Lifeline) — call or text",
        "alt": "You can also use 988lifeline.org for chat."
    },
    "CA": {
        "emergency": "911",
        "crisis": "988 (Suicide Crisis Helpline) — call or text",
        "alt": "Talk Suicide Canada: 1-833-456-4566; text 45645 (hours may vary)."
    },
    "MX": {
        "emergency": "911",
        "crisis": "Línea de la Vida: 800-911-2000",
        "alt": "Chat: saludmental.gob.mx (regional services may vary)."
    },
    "IN": {
        "emergency": "112",
        "crisis": "KIRAN: 1800-599-0019",
        "alt": "AASRA (24x7 volunteer): +91-9820466726."
    },
}


def _hotline_block(country_code: Optional[str]) -> str:
    cc = (country_code or "").upper()
    info = HOTLINES.get(cc)
    if info:
        return (
            f"If you’re in immediate danger, call {info['emergency']}.\n"
            f"You can also reach {info['crisis']}. {info['alt']}"
        )
    return (
        "If you’re in immediate danger, please contact your local emergency number.\n"
        "You can also look up a suicide or crisis hotline in your country."
    )


def _crisis_script(country_code: Optional[str]) -> str:
    """
    Softer, Therabot-style crisis response:
    - Thank the user
    - Validate and express care
    - Provide clear safety guidance
    - Offer to keep talking about staying safe
    """
    return (
        "Therapist:\n"
        "Thank you for telling me how painful things feel right now. "
        "I’m really sorry you’re going through this, and your safety matters a lot. "
        "You shouldn’t have to carry these feelings on your own.\n"
        + _hotline_block(country_code)
        + "\n"
        "I’m only a chat tool and I can’t see how immediate the risk is, "
        "so reaching out to a trusted person or real-time crisis support can be really important.\n"
        "If you’d like, we can also talk about one small step to help you stay even a little safer "
        "in the next hour."
    )


# -----------------------------
# Assistant reply safety scan
# -----------------------------
_REPLY_SELF_HARM_DIRECT = re.compile(
    r"\byou\s+(?:should|could|might want to|may as well|need to|have to)\s+"
    r"(?:kill yourself|end your life|commit suicide|take your own life|"
    r"make it all stop for good)\b",
    re.I,
)

_REPLY_HARM_OTHERS_DIRECT = re.compile(
    r"\b(?:you|u)\s+(?:should|could|might)\s+"
    r"(?:hurt|hit|punch|stab|shoot|kill)\s+(?:him|her|them|someone)\b",
    re.I,
)

_REPLY_METHODS_INSTRUCTIVE = re.compile(
    r"\b(here(?:'s)? how|you can|you just need to)\b.*\b"
    r"(overdose|cut deeper|jump off|hang yourself|poison yourself|"
    r"crash your car)\b",
    re.I | re.DOTALL,
)

_REPLY_CLINICAL_AUTHORITY = re.compile(
    r"\b(I (?:can|will) prescribe|I recommend a dosage of|\btake \d{1,3}\s?mg\b)\b",
    re.I,
)


def _scan_reply_danger(llm_reply: str) -> Dict[str, Any]:
    t = llm_reply or ""
    if not t.strip():
        return {
            "danger": False,
            "crisis_like": False,
            "clinical_overreach": False,
            "reason": "",
        }

    if _REPLY_SELF_HARM_DIRECT.search(t) or _REPLY_METHODS_INSTRUCTIVE.search(t):
        return {
            "danger": True,
            "crisis_like": True,
            "clinical_overreach": False,
            "reason": "assistant_self_harm_direct_or_instructive",
        }

    if _REPLY_HARM_OTHERS_DIRECT.search(t):
        return {
            "danger": True,
            "crisis_like": False,
            "clinical_overreach": False,
            "reason": "assistant_harm_others_direct",
        }

    if _REPLY_CLINICAL_AUTHORITY.search(t):
        return {
            "danger": True,
            "crisis_like": False,
            "clinical_overreach": True,
            "reason": "assistant_clinical_authority",
        }

    return {
        "danger": False,
        "crisis_like": False,
        "clinical_overreach": False,
        "reason": "",
    }


# -----------------------------
# Sentence / token helpers
# -----------------------------
def _sentences(text: str):
    text = (text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def _limit_words(text: str, max_words: int = 120) -> str:
    words = (text or "").split()
    if len(words) <= max_words:
        return text or ""
    return " ".join(words[:max_words]).rstrip() + "…"


_STOPWORDS = {
    "i", "me", "my", "you", "your", "yours",
    "and", "or", "but", "if", "then", "so", "because",
    "a", "an", "the", "to", "of", "in", "on", "for", "with", "at", "by", "from",
    "it", "this", "that", "is", "am", "are", "was", "were", "be", "been", "being",
    "just", "really", "very", "like", "kind", "sort",
}


def _content_tokens(text: str):
    toks = re.findall(r"[a-z']+", (text or "").lower())
    return [t for t in toks if t not in _STOPWORDS]


def _sentence_overlap(u_sent: str, r_sent: str) -> float:
    u = set(_content_tokens(u_sent))
    r = set(_content_tokens(r_sent))
    if not u or not r:
        return 0.0
    return len(u & r) / max(len(r), 1)


def _is_over_mirroring(user_text: str, llm_reply: str, threshold: float = 0.8) -> bool:
    user_sents = _sentences(user_text)
    reply_sents = _sentences(llm_reply)
    if not user_sents or not reply_sents:
        return False

    overlaps = []
    for rs in reply_sents:
        best = max(_sentence_overlap(us, rs) for us in user_sents)
        overlaps.append(best)

    if (
        len(reply_sents) <= 4
        and overlaps
        and sum(o > threshold for o in overlaps) >= max(2, len(reply_sents) - 1)
    ):
        return True
    return False


def _strip_over_mirroring(user_text: str, llm_reply: str, threshold: float = 0.8) -> str:
    user_sents = _sentences(user_text)
    reply_sents = _sentences(llm_reply)
    if not user_sents or not reply_sents:
        return llm_reply or ""

    kept = []
    for rs in reply_sents:
        best = max(_sentence_overlap(us, rs) for us in user_sents)
        if best < threshold:
            kept.append(rs)

    if not kept:
        return ""
    return " ".join(kept).strip()


# -----------------------------
# MI / language hygiene
# -----------------------------
_RX_MULTI_SPACE = re.compile(r"\s+")
_RX_DIAGNOSE = re.compile(
    r"\b(diagnos(e|is|ing)|prescribe|medication advice|clinical treatment)\b", re.I
)
_RX_PROMISES = re.compile(
    r"\b(this will|100%|guarantee|always works)\b",
    re.I,
)
_RX_DIRECTIVE = re.compile(
    r"\byou (should|need to|have to|must|ought to)\b",
    re.I,
)


def _soften_language(text: str) -> str:
    def repl(match: re.Match) -> str:
        return "you might"

    t = text or ""
    t = _RX_DIRECTIVE.sub(repl, t)
    t = _RX_MULTI_SPACE.sub(" ", t)
    return t.strip()


_RX_SPECULATION = re.compile(
    r"\b(you (?:always|never) feel|you just want|deep down you|"
    r"you only care about)\b",
    re.I,
)


def _reduce_speculation(text: str) -> str:
    sents = _sentences(text)
    cleaned = []
    for s in sents:
        if _RX_SPECULATION.search(s):
            continue
        cleaned.append(s)
    return " ".join(cleaned).strip()


# -----------------------------
# MI scaffolding helpers
# -----------------------------
_REFLECTION_TEMPLATES = [
    "It sounds like you’ve been carrying a lot of {emotion} around this.",
    "I hear that there’s been a lot of {emotion} in this for you.",
    "From what you’ve shared, this has brought up a lot of {emotion}.",
]

_NEUTRAL_REFLECTION_TEMPLATES = [
    "It sounds like this has been a lot to carry.",
    "I hear how big this feels for you.",
    "From what you’ve shared, this has been weighing on you.",
]

_OPEN_QUESTION_TEMPLATES = [
    "What feels most important for you to talk about next?",
    "What’s one part of this you’d like to explore a bit more?",
    "As you notice all of this, what feels like the next small step?",
]

_TINY_STEP_TEMPLATES = [
    "If it feels okay, what is one small thing you might do after this chat to take care of yourself?",
    "Would it help to think about one tiny step that could make tonight a little easier?",
    "If you had to pick one small, manageable action for yourself, what might that be?",
]


def _has_reflection(text: str) -> bool:
    """
    Detects existing MI-style reflections.
    We include variants like:
      - "Therapist: It sounds..."
      - "It sounds really tough..."
      - "It seems like..."
      - "You’re feeling..."
      - "I hear..."
      - "From what you’ve shared..."
    """
    for s in _sentences(text):
        ls = s.lower().strip()
        if ls.startswith("therapist:"):
            ls = ls[len("therapist:"):].strip()

        if (
            ls.startswith("it sounds like")
            or ls.startswith("it sounds ")
            or ls.startswith("it seems like")
            or ls.startswith("it seems ")
            or "you’re feeling" in ls
            or "you're feeling" in ls
            or "you are feeling" in ls
            or ls.startswith("i hear")
            or "from what you’ve shared" in ls
            or "from what you've shared" in ls
        ):
            return True
    return False


def _has_open_question(text: str) -> bool:
    for s in _sentences(text):
        if "?" not in s:
            continue
        ls = s.lower().strip()
        if ls.startswith(
            ("what", "how", "when", "where", "which", "who", "could", "would")
        ):
            return True
    return False


def _ensure_mi_elements(text: str, emotion_hint: str = "") -> str:
    """
    If no reflection exists, prepend one using either emotion_hint
    or a neutral template.
    """
    sents = _sentences(text)
    has_reflection = _has_reflection(text)

    if not has_reflection:
        emotion = (emotion_hint or "").lower()
        if emotion:
            tpl = random.choice(_REFLECTION_TEMPLATES)
            reflection = tpl.format(emotion=emotion)
        else:
            reflection = random.choice(_NEUTRAL_REFLECTION_TEMPLATES)
        if not sents:
            return reflection
        text = reflection + " " + " ".join(sents)
    return text


def _ensure_at_least_one_open_question(text: str) -> str:
    if _has_open_question(text):
        return text
    sents = _sentences(text)
    q = random.choice(_OPEN_QUESTION_TEMPLATES)
    if not sents:
        return q
    return " ".join(sents + [q])


def _ensure_one_gentle_tiny_step(text: str) -> str:
    """
    Only add a tiny-step prompt if there isn't already something similar.
    """
    sents = _sentences(text)
    if not sents:
        return text or ""

    joined = " ".join(sents).lower()
    if any(kw in joined for kw in ["one small thing", "tiny step", "small, manageable"]):
        return text or ""

    step = random.choice(_TINY_STEP_TEMPLATES)
    return " ".join(sents + [step])


# -----------------------------
# Repetition controls
# -----------------------------
def _dedup_lines(text: str) -> str:
    sents = _sentences(text)
    seen = set()
    out = []
    for s in sents:
        key = s.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return " ".join(out).strip()


def _reduce_repeats(text: str, prev_reply: Optional[str] = None) -> str:
    if not prev_reply:
        return text or ""

    new = (text or "").strip()
    old = prev_reply.strip()
    if not new or not old:
        return new

    def toks(t: str) -> set:
        return set(_content_tokens(t))

    new_toks, old_toks = toks(new), toks(old)
    if not new_toks or not old_toks:
        return new

    jaccard = len(new_toks & old_toks) / max(len(new_toks | old_toks), 1)
    if jaccard > 0.8:
        first = _sentences(new)[:1]
        return " ".join(first).strip() if first else new
    return new


# -----------------------------
# Tier footers
# -----------------------------
def _high_footer(text: str) -> str:
    return (
        (text or "").rstrip()
        + "\n\n"
        + "If things feel more intense or unsafe at any point, it’s okay to reach out to a trusted person "
          "or local crisis support rather than managing this alone."
    )


def _caution_footer(text: str) -> str:
    return (
        (text or "").rstrip()
        + "\n\n"
        + "If this ever feels too heavy to carry on your own, it’s okay to reach out to someone you trust or a professional for extra support."
    )


# -----------------------------
# Hotline hallucination guard
# -----------------------------
_RX_PHONE = re.compile(r"\b\d{2,}[\s\-]?\d{2,}[\s\-]?\d{2,}\b")


def _strip_untrusted_hotlines(text: str) -> str:
    t = text or ""
    lower = t.lower()
    if ("hotline" in lower or "suicide line" in lower) and _RX_PHONE.search(t):
        return (
            "If you’re in immediate danger, please contact your local emergency number. "
            "You can also look up a suicide or crisis line in your country."
        )
    return t


# -----------------------------
# Public entry
# -----------------------------
def enforce(
    user_text: str,
    llm_reply: str,
    risk: Optional[Dict[str, Any]] = None,
    country_code: Optional[str] = None,
    prev_reply: Optional[str] = None,
    **_ignored: Any,
) -> Dict[str, Any]:
    """
    Apply safety + MI style normalization.

    Returns:
      {
        'final': str,
        'action': 'crisis_override' | 'soften' | 'ok' | 'danger_override',
        'notes': str,
        'flags': list[str]
      }
    """
    flags = []

    tier = ((risk or {}).get("tier") or "OK").lower()
    emotion_hint = (risk or {}).get("emotion") or ""

    # ----- Crisis override from user text or tier -----
    if tier == "crisis" or _is_suicidal_text(user_text):
        return {
            "final": _crisis_script(country_code),
            "action": "crisis_override",
            "notes": "Crisis override (risk tier or suicide keywords in user text).",
            "flags": ["user_crisis"],
        }

    # ----- Safety scan on raw LLM reply -----
    raw_reply = (llm_reply or "").strip()
    scan = _scan_reply_danger(raw_reply)

    if scan["danger"]:
        if scan["crisis_like"]:
            return {
                "final": _crisis_script(country_code),
                "action": "crisis_override",
                "notes": f"Crisis override based on assistant reply ({scan['reason']}).",
                "flags": ["assistant_crisis_reply"],
            }

        if scan["clinical_overreach"]:
            safe_msg = (
                "Therapist:\nI can’t give medical, medication, or diagnosis advice. "
                "What I can do is stay with you in what you’re going through and help you "
                "think about next steps you might consider."
            )
            flags.append("clinical_overreach_stripped")
            raw_reply = safe_msg
        else:
            safe_msg = (
                "Therapist:\nI’m not able to support plans to harm yourself or anyone else. "
                "We can instead focus on what you’re feeling and what might make things even a little safer for you."
            )
            flags.append("dangerous_reply_stripped")
            raw_reply = safe_msg

    # ----- Non-crisis transform pipeline -----
    text = raw_reply
    text = _strip_bad_phrases(text)

    # Over-mirroring reduction (before other transforms)
    if _is_over_mirroring(user_text, text):
        text = _strip_over_mirroring(user_text, text)
        flags.append("over_mirroring_reduced")

    # MI structure detection
    has_reflection = _has_reflection(text)
    has_openq = _has_open_question(text)
    tier_norm = tier.lower()

    light_touch = tier_norm in ("ok", "caution") and has_reflection and has_openq

    # 1) Minimal safety cleanup (always)
    text = _soften_language(text)
    text = _RX_DIAGNOSE.sub("I can’t provide a diagnosis or medical advice.", text)
    text = _RX_PROMISES.sub("I’m hopeful this might help.", text)
    text = _reduce_speculation(text)

    if light_touch:
        # ---- LIGHT TOUCH: OK / Caution with good MI structure ----
        text = _dedup_lines(text)
        text = _reduce_repeats(text, prev_reply=prev_reply)
        text = _limit_words(text, max_words=120)
        text = _strip_untrusted_hotlines(text)

        if tier_norm == "high":
            text = _high_footer(text)
            action = "soften"
        elif tier_norm == "caution":
            text = _caution_footer(text)
            action = "soften"
        else:  # ok
            action = "ok"

        flags.append("mi_light_touch")

        return {
            "final": text,
            "action": action,
            "notes": "MI-OK reply; light-touch cleanup only.",
            "flags": flags or ["mi_light_touch"],
        }

    # ---- FULL MI PASS (no MI structure yet or High tier) ----
    text = _ensure_mi_elements(text, emotion_hint=emotion_hint)
    text = _ensure_at_least_one_open_question(text)

    if tier_norm in ("high", "caution"):
        text = _ensure_one_gentle_tiny_step(text)

    text = _dedup_lines(text)
    text = _reduce_repeats(text, prev_reply=prev_reply)
    text = _limit_words(text, max_words=120)
    text = _strip_untrusted_hotlines(text)

    if tier_norm == "high":
        text = _high_footer(text)
        action = "soften"
        flags.append("mi_full_high")
    elif tier_norm == "caution":
        text = _caution_footer(text)
        action = "soften"
        flags.append("mi_full_caution")
    else:
        action = "ok"
        flags.append("mi_full_ok")

    return {
        "final": text,
        "action": action,
        "notes": "Full MI pass applied.",
        "flags": flags,
    }