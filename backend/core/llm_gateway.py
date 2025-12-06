# backend/core/llm_gateway.py
import os
import google.generativeai as genai

def make_gemini(model: str = "gemini-2.0-flash", temperature: float = 0.2, max_output_tokens: int = 450):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set GOOGLE_API_KEY in your environment.")
    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(model)
    generation_config = dict(temperature=temperature, max_output_tokens=max_output_tokens)
    safety_settings = []

    def llm_call(prompt: str) -> str:
        resp = model_obj.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
        return (resp.text or "").strip()

    return llm_call
