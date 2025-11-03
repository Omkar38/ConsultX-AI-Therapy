# ConsultX-AI-Therapy
ConsultX — Retrieval-Augmented Guardrails (RAG) &amp; Guardrail Enforcement Layer Overview  ConsultX prevents over-affirmation and unsafe responses by grounding the LLM in vetted CBT/MI content (RAG) and enforcing post-generation safety checks (Guardrail Enforcement Layer). No fine-tuning required.

# Components
RAG Retriever: Semantic search over CBT-Bench + MI transcripts + psychoeducation.
Hybrid Prompting: CBT reasoning + MI tone (empathetic, non-diagnostic).
Guardrail Enforcement Layer: Post-gen filters, grounding validation, and risk-tier policies.

# Architecture (flow)
User → Risk Analyzer (tier) → RAG retrieval → LLM (hybrid prompt) → Guardrail Enforcement → Safe reply → Session log.

# Risk Tiers (examples)
OK: free text with grounding.
Caution: tighter prompts, shorter replies.
High: template-bounded support; no advice; encourage professional help.
Crisis: no free text; show crisis resources and escalation only.

Policy Config (JSON)
{
  "OK":      { "allow_free_text": true,  "max_tokens": 300 },
  "Caution": { "allow_free_text": true,  "max_tokens": 180 },
  "High":    { "allow_free_text": false, "template": "templates/high_support.txt" },
  "Crisis":  { "redirect": "templates/crisis_resources.txt" }
}

Minimal Usage (pseudo-Python)
risk = risk_analyzer(user_text)        # -> {"tier": "Caution", ...}
ctx  = retrieve_cbt_mi(user_text)      # top-k passages (CBT/MI)
prompt = build_hybrid_prompt(user_text, risk, ctx.cbt, ctx.mi, vars)

raw = llm.invoke(prompt)               # model response
safe = enforce_guardrails(raw, risk, ctx)  # filters + grounding + tier policy
log_session(user_text, ctx, raw, safe, risk)
return safe

# Guardrail Enforcement (what it checks)
Unsafe content: self-harm facilitation, romantic transference, medical/diagnostic claims, over-affirmation.
Grounding: cosine sim between reply and retrieved passages ≥ threshold.
Tier policy: applies templates/redirects for High/Crisis.
Length/style: brief, non-judgmental, non-prescriptive; MI techniques allowed.

# Templates (snippets)
High: “I’m really sorry this is so heavy. You’re not alone. I can’t provide clinical advice here, but we can explore safe next steps together. If you’re in danger or thinking of harming yourself, please contact …”
Crisis: “I’m concerned for your safety. Please contact [hotline/local resource] now or reach out to someone you trust. I won’t continue general conversation while you might be at risk.”

# Data & Models
KB: CBT-Bench (CBT cases), MI conversations, psychoeducational guides.
Embeddings: all-MiniLM-L6-v2 (or vendor equivalent).
LLM: vendor-agnostic; no fine-tuning.

# Storage: ChromaDB (persisted vector store).

# Evaluation
Safety pass rate: % replies passing guardrails.
Grounding score: average similarity to retrieved passages.
Latency: p95 end-to-end.
Manual review: flagged cases (High/Crisis) sampling.

# Privacy
Minimize storage; hash session IDs; redact PII in logs; configurable retention.

# Roadmap
Add model-agnostic moderation (policy LLM or safety API).
Expand curated KB (grief, anxiety, sleep hygiene).
Auto-escalation routing + clinician handoff hooks.

# Disclaimer
ConsultX is a supportive, non-therapeutic assistant. It does not diagnose, treat, or replace professional care. In emergencies, users are redirected to crisis resources.
