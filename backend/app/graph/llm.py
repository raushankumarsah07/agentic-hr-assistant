from __future__ import annotations
from app.config import Settings

def get_llm(settings: Settings):
    """Create the configured chat model; callers can use deterministic paths when no key is present."""
    if settings.llm_provider == "gemini" and settings.google_api_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=settings.gemini_model, google_api_key=settings.google_api_key, temperature=0)
    if settings.groq_api_key:
        from langchain_groq import ChatGroq
        return ChatGroq(model=settings.groq_model, groq_api_key=settings.groq_api_key, temperature=0)
    return None

