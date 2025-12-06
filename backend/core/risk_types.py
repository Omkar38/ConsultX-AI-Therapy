
# ============================================================
# Risk Router / risk_types.py
#
# Responsibilities:
# Strengthened minimal risk detector for RAG (HF-only):
# - Emotion: j-hartmann/emotion-english-distilroberta-base (required)
# - Dimensions: optional zero-shot with facebook/bart-large-mnli, else rich keyword rules
# - Smarter channels: negation/mitigation handling + frequency/severity boosters
# - Outputs: {risk_level, score, emotion, dimension, dimensions_all, confidence, notes}
# This is intentionally lightweight and explainable.
# ============================================================


from typing import Dict, Any, List, Tuple
from transformers import pipeline
import math, re

HF_EMOTION_MODEL = "j-hartmann/emotion-english-distilroberta-base"
ZSL_MODEL = "facebook/bart-large-mnli"   # optional; will fallback if not found

# -------------------- DIMENSIONS --------------------
DIMENSIONS = [
    "Maintaining stable weight",
    "Managing mood",
    "Taking medication as prescribed",
    "Participating primary and mental health care",
    "Organizing personal possessions & doing housework",
    "Talking to other people",
    "Expressing feelings to other people",
    "Managing personal safety",
    "Substance use",
    "Suicidal ideation",
    "Managing risk",
    "Following regular schedule for bedtime & sleeping enough",
    "Maintaining regular schedule for eating",
    "Managing work/school",
    "Managing anxiety",
    "Managing anger",
    "Having work-life balance",
    "Showing up for appointments and obligations",
    "Managing finance and items of value",
    "Getting adequate nutrition",
    "Problem solving and decision making capability",
    "Family support",
    "Family relationship",
    "Alcohol usage",
    "Tobacco usage",
    "Other substances usage",
    "Enjoying personal choices for leisure activities",
    "Creativity",
    "Participation in community",
    "Support from social network",
    "Relationship with friends and colleagues",
    "Managing boundaries in close relationship",
    "Managing sexual safety",
    "Productivity at work or school",
    "Motivation at work or school",
    "Coping skills to de-stress",
    "Exhibiting control over self-harming behaviour",
    "Law-abiding",
    "Managing legal issue",
    "Maintaining personal hygiene",
    "Doing exercises and sports"
]

# -------------------- LEXICONS --------------------
# self-harm / suicidal ideation (direct, high-risk phrases)
LEX_SELF_HARM_POS = [
    r"\bkill myself\b",
    r"\bsuicide\b",
    r"\bsuicidal\b",
    # “end(ing) my life / end it all”
    r"\bend my life\b",
    r"\bending my life\b",
    r"\b(end|ending) it all\b",
    # explicit wish to die
    r"\bi want to die\b",
    r"\bi just want to die\b",
    # hopelessness about living
    r"\bno reason to live\b",
    r"\bbetter off dead\b",
    r"\bi don['’]t want to live\b",
    # “no future for myself/me”
    r"\bdon['’]t see a future for (myself|me)\b",
    # generic self-harm / cutting
    r"\bself[- ]?harm\b",
    r"\bhurt myself\b",
    r"\bcut(ting)? myself\b",
]
# mitigation (reduce risk if present)
LEX_SELF_HARM_MITIG = [
    # explicit denials of self-harm intent
    r"\bnot trying to (kill|hurt) myself\b",
    r"\bnot going to (kill|hurt) myself\b",
    r"\bno intention of (killing|hurting) myself\b",
    r"\bwould never (kill|hurt) myself\b",
    r"\bi (am|m) safe right now\b",
    r"\bi (am|m) not going to do anything\b",
    r"\bi (am|m) not going to act on (it|these thoughts)\b",
    r"\bi won'?t act on (it|these thoughts)\b",
]
LEX_HELP_SEEKING = [
    r"\bseeking help\b",
    r"\breach(ed)? out\b",
    r"\bcalled (a )?hotline\b",
    r"\btalking to (a )?(therapist|counsel(or|ler)|friend|family)\b",
]



# substance
LEX_SUBSTANCE_POS = [
    r"\bdrink(ing)?\b", r"\balcohol\b", r"\bbinge\b",
    r"\bdrunk\b|\bblackout\b|\bhangover\b",
    r"\bshots?\b|\bwhiskey\b|\bvodka\b|\btequila\b",
    r"\bweed\b|\bcannabis\b|\bmarijuana\b",
    r"\bcoke\b|\bcocaine\b|\bopioid(s)?\b|\bbenz(o|odiazepine)s?\b",
    r"\bhigh\b|\bstoned\b"
]
LEX_SUBSTANCE_NEG = [  # reduce risk when negated/mitigated
    r"\bquit (drinking|alcohol|weed|coke|opioids?)\b",
    r"\bstopped (drinking|using)\b", r"\bcut(ting)? down\b",
    r"\bsober\b", r"\bclean\b"
]

# functioning
LEX_FUNCTIONING_POS = [
    r"\bcan('?|no)t (work|focus|sleep|eat|get up|cope)\b",
    r"\binsomnia\b", r"\bno energy\b", r"\bexhausted\b",
    r"\bmiss(ed)? (class|work|appointments?)\b"
]
LEX_FUNCTIONING_NEG = [
    r"\bmanaging\b", r"\bkeeping up\b", r"\bdoing okay\b"
]

# anxiety / fear
LEX_ANXIETY_POS = [
    r"\bpanic attacks?\b", r"\bconstant worry\b", r"\bracing thoughts\b",
    r"\bterrified\b", r"\bafraid\b", r"\bscared\b"
]

# anger / aggression
LEX_ANGER_POS = [
    r"\brage\b", r"\bfurious\b", r"\bso mad\b", r"\bwant to hit\b",
    r"\bwant to (hurt|punch)\b"
]

# relationship / social
LEX_RELATIONSHIP = [
    r"\bmy (partner|girlfriend|boyfriend|husband|wife)\b",
    r"\bmy friends?\b", r"\bmy family\b", r"\bparents\b",
    r"\broommate\b", r"\bcolleague\b"
]

# financial / legal
LEX_FINANCE = [
    r"\bdebt\b", r"\bbills\b", r"\brate\b", r"\brent\b", r"\bloans?\b",
    r"\bcredit card\b", r"\bcollections\b"
]
LEX_LEGAL = [
    r"\barrest(ed)?\b", r"\bcourt\b", r"\bcharges?\b", r"\bprobation\b"
]

# sleep / appetite / weight
LEX_SLEEP = [
    r"\bcannot sleep\b", r"\binsomnia\b", r"\bsleep(ing)? only (2|3|4) hours\b",
]
LEX_APPETITE = [
    r"\bno appetite\b", r"\bnot eating\b", r"\bovereating\b", r"\bbinge eating\b"
]
LEX_WEIGHT = [
    r"\bweight (loss|gain)\b", r"\blost \d+ (pounds|lbs|kg)\b"
]

# -------------------- HELPERS --------------------
def _hits(text: str, patterns: List[str]) -> int:
    """Count regex hits in text."""
    return sum(bool(re.search(p, text)) for p in patterns)


def _any(text: str, patterns: List[str]) -> bool:
    return _hits(text, patterns) > 0


def _apply_mitigation(score: float, text: str, mitigators: List[str]) -> float:
    """Reduce score when mitigation phrases appear."""
    if _any(text, mitigators):
        return score * 0.5
    return score


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


# -------------------- MODEL WRAPPERS --------------------
_emotion_pipe = pipeline("text-classification", model=HF_EMOTION_MODEL, return_all_scores=True)

try:
    _zsl_pipe = pipeline("zero-shot-classification", model=ZSL_MODEL)
except Exception:
    _zsl_pipe = None


def _emotion(text: str) -> Tuple[str, float, Dict[str, float]]:
    """Return (top_label, top_score, full_dist)."""
    if not text.strip():
        return "neutral", 0.0, {}
    out = _emotion_pipe(text)[0]
    # out: list of dicts {label, score}
    dist = {d["label"].lower(): float(d["score"]) for d in out}
    label = max(dist, key=dist.get)
    return label, dist[label], dist


def _zsl_dimensions(text: str) -> List[Tuple[str, float]]:
    """Optional zero-shot over DIMENSIONS, else [] on failure."""
    if not text.strip():
        return []
    if _zsl_pipe is None:
        return []
    try:
        res = _zsl_pipe(
            text,
            candidate_labels=DIMENSIONS,
            multi_label=True
        )
        # Some HF versions return list, some dict
        if isinstance(res, list):
            res = res[0]
        labels = res.get("labels", [])
        scores = res.get("scores", [])
        return list(zip(labels, scores))
    except Exception:
        return []


# -------------------- DIM RULES (keyword-based) --------------------
def _dimrules(text: str) -> List[str]:
    """Cheap rules to guess dimensions when ZSL is absent or low-confidence."""
    t = text.lower()
    dims = []

    # suicidality / self-harm
    if _any(t, LEX_SELF_HARM_POS):
        dims.append("Suicidal ideation")
        dims.append("Managing personal safety")

    # substance
    if _any(t, LEX_SUBSTANCE_POS):
        dims.append("Substance use")
        if re.search(r"\balcohol\b|\bwhiskey\b|\bvodka\b|\btequila\b|\bbeer\b|\bwine\b", t):
            dims.append("Alcohol usage")
        if re.search(r"\bweed\b|\bcannabis\b|\bmarijuana\b", t):
            dims.append("Other substances usage")

    # functioning
    if _any(t, LEX_FUNCTIONING_POS):
        dims.append("Managing work/school")
        dims.append("Managing risk")

    # anxiety / fear
    if _any(t, LEX_ANXIETY_POS):
        dims.append("Managing anxiety")

    # anger
    if _any(t, LEX_ANGER_POS):
        dims.append("Managing anger")

    # relationships
    if _any(t, LEX_RELATIONSHIP):
        dims.append("Relationship with friends and colleagues")
        dims.append("Relationship with family")

    # finance / legal
    if _any(t, LEX_FINANCE):
        dims.append("Managing finance and items of value")
    if _any(t, LEX_LEGAL):
        dims.append("Managing legal issue")
        dims.append("Managing risk")

    # sleep / appetite / weight
    if _any(t, LEX_SLEEP):
        dims.append("Following regular schedule for bedtime & sleeping enough")
        dims.append("Managing work/school")
    if _any(t, LEX_APPETITE):
        dims.append("Maintaining regular schedule for eating")
        dims.append("Maintaining stable weight")
    if _any(t, LEX_WEIGHT):
        dims.append("Maintaining stable weight")

    # de-duplicate
    seen = set()
    out = []
    for d in dims:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


# -------------------- RISK SCORING --------------------
def assess(text: str) -> Dict[str, Any]:
    """
    Main entry:
      Returns:
        {
          "risk_level": "OK" | "Caution" | "High" | "Crisis",
          "tier": same as risk_level (for compatibility),
          "score": float in [0, 3],
          "emotion": top emotion label or None,
          "dimension": top dimension (if any),
          "dimensions": list of dimensions (deduped),
          "confidence": float in [0,1],
          "notes": list of strings about how we decided
        }
    """
    raw = text or ""
    t_lower = raw.lower()
    notes: List[str] = []

    # 1) Emotion model
    emo_label, emo_score, emo_dist = _emotion(raw)
    notes.append(f"emotion={emo_label}:{emo_score:.2f}")
    negative_emotions = {"sadness", "fear", "anger", "disgust"}
    is_negative = emo_label in negative_emotions and emo_score >= 0.40

    # 2) Self-harm heuristic channel (raw)
    self_harm_hits = _hits(t_lower, LEX_SELF_HARM_POS)
    self_harm_prob = 1.0 if self_harm_hits > 0 else 0.0
    if self_harm_hits > 0:
        notes.append(f"self_harm_hits={self_harm_hits}")

    # 3) Substance / functioning boosters
    substance_hits = _hits(t_lower, LEX_SUBSTANCE_POS)
    func_hits = _hits(t_lower, LEX_FUNCTIONING_POS)
    if substance_hits:
        notes.append(f"substance_hits={substance_hits}")
    if func_hits:
        notes.append(f"functioning_hits={func_hits}")

    # 4) Mitigation phrases (explicit denial of intent)
    mitig_hits = _hits(t_lower, LEX_SELF_HARM_MITIG)
    self_harm_prob = _apply_mitigation(self_harm_prob, t_lower, LEX_SELF_HARM_MITIG)
    if mitig_hits > 0:
        notes.append("mitigation_present")

    # 5) Help-seeking (DOES NOT cancel crisis; just logged)
    try:
        help_hits = _hits(t_lower, LEX_HELP_SEEKING)
    except NameError:
        help_hits = 0
    if help_hits > 0:
        notes.append(f"help_seeking_hits={help_hits}")

    # 6) Dimensions via ZSL + rules
    zsl_dims = _zsl_dimensions(raw)
    rule_dims = _dimrules(raw)
    dims_all: List[Tuple[str, float]] = []

    if zsl_dims:
        # keep ones with score >= 0.30
        dims_all.extend([(d, s) for d, s in zsl_dims if s >= 0.30])
        notes.append("zsl_dims_used")
    else:
        notes.append("zsl_unavailable")

    for d in rule_dims:
        # rule-based dims get a nominal score
        dims_all.append((d, 0.35))

    # dedupe by label, keep max score
    dim_scores: Dict[str, float] = {}
    for d, s in dims_all:
        prev = dim_scores.get(d, 0.0)
        if s > prev:
            dim_scores[d] = s

    dim_list = sorted(dim_scores.items(), key=lambda x: x[1], reverse=True)
    dimensions = [d for d, _ in dim_list]
    top_dimension = dimensions[0] if dimensions else None
    if top_dimension:
        notes.append(f"top_dimension={top_dimension}")

    # 7) Aggregate risk score (0–3)
    score = 0.0

    if is_negative:
        score += 1.0
        notes.append("negative_emotion")

    # Self-harm channel only if NOT mitigated
    if self_harm_prob >= 0.5 and mitig_hits == 0:
        score += 2.0
        notes.append("self_harm_channel")

    if substance_hits:
        score += 0.5
    if func_hits:
        score += 0.5

    # dimension-based bumps
    if any(d in ("Suicidal ideation", "Managing personal safety") for d in dimensions):
        score += 1.0
        notes.append("dimension_suicide_or_safety")

    if any(d in ("Substance use", "Alcohol usage") for d in dimensions):
        score += 0.5
        notes.append("dimension_substance")

    score = _clamp(score, 0.0, 3.0)

    # If we have mitigation + suicide/safety dims and reduced self_harm_prob,
    # cap at High (<= 2.0) instead of Crisis.
    if mitig_hits > 0 and "dimension_suicide_or_safety" in notes and self_harm_prob < 0.7:
        score = min(score, 2.0)

    # 8) Map to risk level
    raw_self_harm_hits = self_harm_hits
    crisis_override = False

    # Crisis override ONLY if high probability and NO mitigation
    if self_harm_prob >= 0.85 and mitig_hits == 0:
        crisis_override = True
        notes.append("crisis_override_prob")
    # Or raw suicidal language without mitigation (e.g., "I want to die")
    elif raw_self_harm_hits > 0 and mitig_hits == 0:
        crisis_override = True
        notes.append("crisis_override_lexical")

    if crisis_override:
        risk_level = "Crisis"
    else:
        if score < 1.0:
            risk_level = "OK"
        elif score < 2.0:
            risk_level = "Caution"
        elif score < 3.0:
            risk_level = "High"
        else:
            # score == 3.0 without crisis_override → treat as High severity but non-crisis
            risk_level = "High"

    # 9) confidence: sigmoid-ish over score
    confidence = 1 / (1 + math.exp(-(score - 1.0)))  # ~0.27 at 0, ~0.73 at 2, ~0.88 at 3

    return {
        "risk_level": risk_level,
        "tier": risk_level,
        "score": float(score),
        "emotion": emo_label if emo_dist else None,
        "dimension": top_dimension,
        "dimensions": dimensions,
        "confidence": float(confidence),
        "notes": notes,
    }



if __name__ == "__main__":
    # quick manual check
    xs = [
        "I'm fine, just tired from work and want to relax.",
        "Sometimes I think about ending my life, I don't see a future for myself.",
        "I got so drunk last night I blacked out, this keeps happening.",
        "I haven't slept well in weeks and I can't focus in class.",
        "My friends all stopped talking to me and I feel completely alone.",
        "I used to self-harm but I'm in therapy now and haven't done it in months.",
        "Work was stressful but I finished my tasks. I think I'm okay.",
        "I hear voices in my head telling me things in different languages.",
        "I haven't been sleeping much for the last two weeks, completely exhausted, might quit my job.",
        "I quit drinking last month and I'm trying to stay sober."
    ]
    for x in xs:
        print("\nTEXT:", x)
        print(assess(x))
