"""AI Advisor Service — Groq integration for intelligent financial advice."""

import json
import os
import logging
from sqlalchemy.orm import Session

from app.fastapi_app.core.config import settings
from app.fastapi_app.schemas.advisor import AdvisorRequest, AdvisorResponse
from app.fastapi_app.services.advisor_context_service import AdvisorContextService

logger = logging.getLogger(__name__)

try:
    from groq import Groq
except ImportError:
    Groq = None


class AdvisorService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.context_service = AdvisorContextService(session)

    def get_context_summary(self, user_id: int) -> dict:
        return self.context_service.get_context(user_id)

    def ask_advisor(self, user_id: int, payload: AdvisorRequest) -> AdvisorResponse:
        context = self.get_context_summary(user_id)
        
        # Format history if provided
        history_text = ""
        if payload.history:
            snippets = [f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}" for msg in payload.history[-6:]]
            history_text = "\n".join(snippets)

        prompt = f"""You are LedgerBud's personal financial advisor.
Your primary goal is to provide specific, data-backed financial advice using ONLY the provided context.
NEVER make up numbers. Use exact figures from the context.
Keep your response concise, using short bullet points where appropriate. Include one clear recommendation.
If the data is insufficient to answer the question, state exactly what is missing.

Financial Context (JSON):
{json.dumps(context, indent=2, default=str)}

Recent Conversation History:
{history_text or 'No prior messages.'}

User Question:
{payload.question}
"""

        api_key = getattr(settings, "groq_api_key", os.environ.get("GROQ_API_KEY", ""))
        
        if not api_key:
            return AdvisorResponse(
                answer="The Groq API key is not configured. Please add GROQ_API_KEY to your environment variables to enable the AI advisor.",
                context_summary=context,
                provider="fallback_no_key"
            )

        if Groq is None:
            return AdvisorResponse(
                answer="The 'groq' Python package is not installed. Please run `pip install groq` to enable the AI advisor.",
                context_summary=context,
                provider="fallback_no_pkg"
            )

        try:
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are LedgerBud, a precise and highly analytical personal finance advisor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1024,
                timeout=15.0
            )
            
            answer = completion.choices[0].message.content.strip()
            return AdvisorResponse(
                answer=answer,
                context_summary=context,
                provider="groq_llama_3.1"
            )
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return AdvisorResponse(
                answer="I'm currently unable to process your request due to an AI service error. Please try again later.",
                context_summary=context,
                provider="error"
            )
