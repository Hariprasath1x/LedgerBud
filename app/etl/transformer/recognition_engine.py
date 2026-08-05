"""
Merchant Recognition Engine for AI Financial Intelligence Pipeline.
Implements a strict priority hierarchy for merchant recognition:
1. Unique Identifier Match
2. Merchant Memory
3. Known Merchant Database
4. AI Pattern Recognition
5. Unknown
"""

from typing import Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.fastapi_app.models.merchant import Merchant
from app.intelligence.merchant_dict import MERCHANT_SEED_DATA
from app.etl.transformer.normalizer import extract_structured_tokens

@dataclass
class RecognitionDecision:
    merchant_id: Optional[int]
    canonical_name: str
    category: str
    confidence_score: int
    recognition_source: str
    matching_method: str
    reason_for_decision: str
    unique_identifier: Optional[str]


class MerchantRecognitionEngine:
    def __init__(self, session: Session, user_id: int):
        self.session = session
        self.user_id = user_id
        self._build_seed_lookup()

    def _build_seed_lookup(self):
        """Build a fast lookup dictionary from MERCHANT_SEED_DATA."""
        self.known_merchants = {}
        for canonical, category, keywords in MERCHANT_SEED_DATA:
            for kw in keywords:
                self.known_merchants[kw.lower()] = (canonical, category)

    def recognize(self, raw_description: str, normalized_description: str) -> RecognitionDecision:
        if not raw_description:
            return self._unknown_decision(raw_description)

        tokens = extract_structured_tokens(raw_description)
        unique_id = tokens.get("upi_id") or tokens.get("vpa") or tokens.get("merchant_id")

        # Priority 1 & 2: Unique Identifier Match & Merchant Memory
        if unique_id:
            memory_match = self._check_merchant_memory_by_id(unique_id)
            if memory_match:
                return RecognitionDecision(
                    merchant_id=memory_match.id,
                    canonical_name=memory_match.display_name,
                    category=memory_match.category or "Unknown",
                    confidence_score=100,
                    recognition_source="Merchant Memory",
                    matching_method="Exact Unique ID Match",
                    reason_for_decision=f"Matched known unique identifier: {unique_id}",
                    unique_identifier=unique_id
                )

        # Still check Merchant Memory but via fuzzy name/description match if no unique_id
        # (For now, we strictly use unique_id for 100% confidence memory match.
        # Name-based memory matches can be tricky due to display name ambiguity - Principle 2)
        
        # Priority 3: Known Merchant Database
        seed_match = self._check_known_database(normalized_description, raw_description)
        if seed_match:
            canonical_name, category, matched_keyword = seed_match
            return RecognitionDecision(
                merchant_id=None,
                canonical_name=canonical_name,
                category=category,
                confidence_score=98,
                recognition_source="Known Merchant Database",
                matching_method="Keyword Match",
                reason_for_decision=f"Matched known merchant keyword: '{matched_keyword}'",
                unique_identifier=unique_id
            )

        # Priority 4: AI Pattern Recognition (Heuristics for now, LLM can be plugged here later)
        # We will extract readable names for fallback
        heuristic_name = self._extract_readable_name(normalized_description)
        if heuristic_name and len(heuristic_name) > 3 and not heuristic_name.isnumeric():
            return RecognitionDecision(
                merchant_id=None,
                canonical_name=heuristic_name,
                category="Unknown",
                confidence_score=85,
                recognition_source="AI Pattern Recognition (Heuristic)",
                matching_method="Token Extraction",
                reason_for_decision="Extracted likely merchant name from description structure.",
                unique_identifier=unique_id
            )

        # Priority 5: Unknown Merchant
        return self._unknown_decision(raw_description, unique_id)

    def _check_merchant_memory_by_id(self, unique_id: str) -> Optional[Merchant]:
        return self.session.scalar(
            select(Merchant).where(
                Merchant.user_id == self.user_id,
                Merchant.unique_identifier == unique_id
            )
        )

    def _check_known_database(self, normalized_desc: str, raw_desc: str) -> Optional[tuple]:
        search_space = (normalized_desc + " " + raw_desc).lower()
        
        # Sort keywords by length descending to match longest phrases first (e.g. "amazon prime" before "amazon")
        sorted_keywords = sorted(self.known_merchants.keys(), key=len, reverse=True)
        
        for kw in sorted_keywords:
            if kw in search_space:
                canonical, cat = self.known_merchants[kw]
                return canonical, cat, kw
        return None
        
    def _extract_readable_name(self, description: str) -> str:
        """Fallback to extract a human-readable merchant name from cleaned description."""
        words = description.split()
        readable = []
        for word in words[:3]:
            if len(word) > 2 and not word.isdigit() and "UPI" not in word and "IMPS" not in word and "NEFT" not in word:
                readable.append(word.title())
        return ' '.join(readable) if readable else "Unknown"

    def _unknown_decision(self, raw_description: str, unique_id: Optional[str] = None) -> RecognitionDecision:
        return RecognitionDecision(
            merchant_id=None,
            canonical_name="Unknown Merchant",
            category="Unknown",
            confidence_score=40,
            recognition_source="Fallback",
            matching_method="None",
            reason_for_decision="Insufficient evidence to identify merchant.",
            unique_identifier=unique_id
        )
