"""
risk_analyzer.py
Risk Analyzer:
- Emotion detection using pretrained HF model
- Dimension + Score classification via OpenAI few-shot prompt (optional)
- Rule-based fallback classifier (if no API)
- Risk level computation
- SQLite storage for history
"""

from typing import Dict, List, Any, Tuple
import sqlite3
import json
import time
import re
import os

# === Optional: OpenAI (few-shot) ===
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# === Transformers Emotion pipeline ===
try:
    from transformers import pipeline
    EMOTION_AVAILABLE = True
except Exception:
    EMOTION_AVAILABLE = False

# === Basic config ===
DB_PATH = "risk_analyzer_history.db"
EMOTION_MODEL = "j-hartmann/emotion-english-distilroberta-base"  # HF model

# === Dimensions list (37) - keep exactly as in the paper or adapt ===
DIMENSIONS = [
 "Maintaining stable weight",
 "Managing mood",
 "Taking medication as prescribed",
 "Participating primary and mental health care",
 "Organizing personal possessions & doing housework",
 "Talking to other people",
 "Expressing feelings to other people",
 "Managing personal safety",
 "Managing risk",
 "Following regular schedule for bedtime & sleeping enough",
 "Maintaining regular schedule for eating",
 "Managing work/school",
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

# === Initialize emotion pipeline ===
_emotion_pipeline = None
def get_emotion_pipeline():
    global _emotion_pipeline
    if _emotion_pipeline is None:
        if not EMOTION_AVAILABLE:
            raise RuntimeError("transformers not installed. pip install transformers")
        _emotion_pipeline = pipeline("text-classification", model=EMOTION_MODEL)
    return _emotion_pipeline

# === SQLite setup ===
def init_db(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS risk_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL,
        user_text TEXT,
        dimension TEXT,
        score INTEGER,
        emotion TEXT,
        risk_level TEXT,
        confidence REAL,
        meta TEXT
    )
    """)
    conn.commit()
    conn.close()

# === Helper: simple text normalization ===
def clean_text(t: str) -> str:
    return re.sub(r"\s+", " ", t.strip())

# === Emotion detection ===
def detect_emotion(text: str) -> Dict[str,Any]:
    """
    Returns top emotion label and score.
    Uses HF pipeline model (pretrained).
    """
    text = clean_text(text)
    if not EMOTION_AVAILABLE:
        # fallback: rule-based microsignal
        lowered = text.lower()
        if any(w in lowered for w in ["sad", "depressed", "hopeless", "suicid"]): return {"label":"sadness","score":0.9}
        if any(w in lowered for w in ["angry","rage","hate"]): return {"label":"anger","score":0.9}
        if any(w in lowered for w in ["anx","nervous","worried","panic"]): return {"label":"anxiety","score":0.85}
        return {"label":"neutral","score":0.6}
    pipe = get_emotion_pipeline()
    res = pipe(text)
    if isinstance(res, list) and len(res) > 0:
        return {"label": res[0]["label"], "score": float(res[0].get("score", 0))}
    else:
        return {"label":"neutral","score":0.5}

# === Few-shot prompt classification (OpenAI) ===
from prompts import DIMENSION_PROMPT_TEMPLATE

def classify_with_openai(user_text: str, openai_api_key: str = None, model: str="gpt-3.5-turbo") -> Dict[str,Any]:
    """
    Sends a few-shot prompt to OpenAI to get (dimension, score).
    Returns {'dimensions': [...], 'score': int, 'confidence': float}
    """
    if not OPENAI_AVAILABLE:
        raise RuntimeError("OpenAI SDK not installed (openai).")
    if openai_api_key is None:
        openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key is None:
        raise RuntimeError("No OpenAI API key provided.")

    openai.api_key = openai_api_key

    DIMENSION_LIST = "\n".join([f"{i+1}. {d}" for i, d in enumerate(DIMENSIONS)])
    prompt = DIMENSION_PROMPT_TEMPLATE.replace("<<USER_TEXT>>", user_text)
    prompt = prompt.replace("... (use full list from system)", DIMENSION_LIST)

    # Use chat completion
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[{"role":"system","content":"You are an assistant that maps user text to one or more daily-functioning dimensions and assigns a single score 0/1/2."},
                  {"role":"user","content": prompt}],
        temperature=0.0,
        max_tokens=300
    )
    text = resp["choices"][0]["message"]["content"].strip()
    # Expected output format (we enforce in prompt): JSON like {"dimensions": ["Sleep"], "score": 2}
    # Try to parse JSON inside text
    try:
        # try extract JSON substring
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != -1:
            parsed = json.loads(text[start:end])
        else:
            parsed = json.loads(text)
    except Exception:
        # best-effort parse: look for "Dimension:" and "Score:"
        dims = []
        score = None
        for line in text.splitlines():
            if "Dimension" in line or "dimension" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    dims.append(parts[1].strip())
            if "Score" in line or "score" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    try:
                        score = int(re.findall(r"\d+", parts[1])[0])
                    except:
                        pass
        parsed = {"dimensions": dims or ["Unknown"], "score": score if score is not None else 1}
    # heuristic confidence
    confidence = 0.9
    parsed.setdefault("confidence", confidence)
    return parsed

# === Rule-based fallback classifier ===
SIMPLE_KEYWORD_DIMENSION_MAP = {
    "sleep": ["Following regular schedule for bedtime & sleeping enough",],
    "sleeping": ["Following regular schedule for bedtime & sleeping enough",],
    "eat": ["Maintaining regular schedule for eating", "Getting adequate nutrition"],
    "hungry": ["Maintaining regular schedule for eating"],
    "work": ["Managing work/school", "Productivity at work or school"],
    "job": ["Managing work/school"],
    "drink": ["Alcohol usage"],
    "alcohol": ["Alcohol usage"],
    "smoke": ["Tobacco usage"],
    "friends": ["Talking to other people", "Relationship with friends and colleagues"],
    "hygiene": ["Maintaining personal hygiene"],
    "shower": ["Maintaining personal hygiene"],
    "suicide": ["Exhibiting control over self-harming behaviour"],
    "harm": ["Exhibiting control over self-harming behaviour", "Managing personal safety"],
    "motivat": ["Motivation at work or school"],
    "creative": ["Creativity"],
    "stress": ["Coping skills to de-stress", "Managing mood"],
    "anx": ["Managing mood"],
    "depress": ["Managing mood"],
    "medicat": ["Taking medication as prescribed"],
    "appointments": ["Showing up for appointments and obligations"],
    "finance": ["Managing finance and items of value"],
    # add more as needed
}

def rule_based_dimension_and_score(text: str, emotion_label: str) -> Dict[str,Any]:
    txt = text.lower()
    found_dims = []
    for k,v in SIMPLE_KEYWORD_DIMENSION_MAP.items():
        if k in txt:
            for d in v:
                if d not in found_dims:
                    found_dims.append(d)
    # default
    if not found_dims:
        found_dims = ["Managing mood"]

    # simple scoring heuristics
    score = 1
    if emotion_label in ["sadness","anger","fear","disgust","anxiety"]:
        if any(w in txt for w in ["can’t", "cannot", "hopeless", "suicide", "kill myself", "want to die"]):
            score = 2
        else:
            score = 1
    else:
        score = 0
    # adjust score on strong keywords
    if any(w in txt for w in ["quit my job", "lost my job", "no food", "homeless", "kick out"]):
        score = 2

    return {"dimensions": found_dims, "score": score, "confidence": 0.6}

# === Risk Level computation ===
def compute_risk_level(score:int, emotion_label:str, emotion_score:float) -> str:
    if score == 2:
        # critical always high
        return "high"
    if score == 1:
        # if strong negative emotion -> high, else medium
        if emotion_label in ["sadness","anger","fear","disgust","anxiety"] and emotion_score >= 0.7:
            return "high"
        return "medium"
    return "low"

# === Main analyze function ===
def analyze_text(user_text: str, openai_api_key: str = None, use_openai: bool = True, openai_model: str = "gpt-3.5-turbo") -> Dict[str,Any]:
    """
    Full pipeline:
    - emotion detection
    - (dimension, score) via OpenAI or fallback rule-based
    - risk computation
    - persist to sqlite
    """
    init_db()  # ensure DB exists
    t = clean_text(user_text)
    emotion_res = detect_emotion(t)
    emotion_label = emotion_res["label"]
    emotion_conf = emotion_res.get("score", 0.0)

    classification = None
    if use_openai and OPENAI_AVAILABLE:
        try:
            classification = classify_with_openai(t, openai_api_key=openai_api_key, model=openai_model)
        except Exception as e:
            # fallback
            classification = rule_based_dimension_and_score(t, emotion_label)
            classification["meta_error"] = str(e)
    else:
        classification = rule_based_dimension_and_score(t, emotion_label)

    dims = classification.get("dimensions", ["Managing mood"])
    score = int(classification.get("score", 1))
    confidence = float(classification.get("confidence", 0.6))

    risk_level = compute_risk_level(score, emotion_label, emotion_conf)

    record = {
        "timestamp": time.time(),
        "user_text": user_text,
        "dimension": dims[0] if isinstance(dims, list) and len(dims) > 0 else dims,
        "score": score,
        "emotion": emotion_label,
        "risk_level": risk_level,
        "confidence": confidence,
        "meta": json.dumps({"all_dimensions": dims, **{k:v for k,v in classification.items() if k not in ['dimensions','score','confidence']}})
    }

    # store
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT INTO risk_history (timestamp, user_text, dimension, score, emotion, risk_level, confidence, meta)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (record["timestamp"], record["user_text"], record["dimension"], record["score"], record["emotion"], record["risk_level"], record["confidence"], record["meta"]))
    conn.commit()
    conn.close()

    return {"dimension_list": dims, "selected_dimension": record["dimension"], "score": score, "emotion": emotion_label, "emotion_conf": emotion_conf, "risk_level": risk_level, "confidence": confidence}
