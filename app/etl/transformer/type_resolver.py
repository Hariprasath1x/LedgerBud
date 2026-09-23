import re
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

@dataclass
class TypeResolution:
    transaction_type: str  # "Credit", "Debit", "Unknown", "Conflict"
    confidence_score: int
    resolution_source: str
    amount: Decimal

class TransactionTypeResolver:
    def __init__(self, tolerance: float = 0.05):
        self.tolerance = Decimal(str(tolerance))
        
        # Regex to match CR/DR tokens
        # We match it if it starts the string or is preceded by a slash or space,
        # and ends the string or is followed by a slash or space.
        self.marker_pattern = re.compile(r'(?:^|/|\s)(CR|DR)(?:/|\s|$)', re.IGNORECASE)

    def resolve(
        self,
        raw_description: str,
        debit_str: Optional[str],
        credit_str: Optional[str],
        amount_str: Optional[str],
        previous_balance: Optional[Decimal],
        current_balance: Optional[Decimal]
    ) -> TypeResolution:
        from app.etl.transformer.normalizer import parse_amount
        
        debit_amount = parse_amount(debit_str) if debit_str else None
        credit_amount = parse_amount(credit_str) if credit_str else None
        generic_amount = parse_amount(amount_str) if amount_str else None
        
        # 1. Gather all potential signals
        signals = {}
        
        # A. Marker Signal
        marker_match = self.marker_pattern.search(raw_description or '')
        if marker_match:
            marker = marker_match.group(1).upper()
            signals['marker'] = 'Credit' if marker == 'CR' else 'Debit'
            
        # B. Column Signal
        if debit_amount and debit_amount > 0 and not credit_amount:
            signals['column'] = 'Debit'
        elif credit_amount and credit_amount > 0 and not debit_amount:
            signals['column'] = 'Credit'
            
        # Determine the effective amount to use for balance reconciliation
        eff_amount = generic_amount or debit_amount or credit_amount or Decimal('0.00')
        
        # C. Balance Signal
        if previous_balance is not None and current_balance is not None and eff_amount > 0:
            diff_credit = abs((previous_balance + eff_amount) - current_balance)
            diff_debit = abs((previous_balance - eff_amount) - current_balance)
            
            if diff_credit <= self.tolerance and diff_debit > self.tolerance:
                signals['balance'] = 'Credit'
            elif diff_debit <= self.tolerance and diff_credit > self.tolerance:
                signals['balance'] = 'Debit'
                
        # 2. Reconcile signals
        if not signals:
            return TypeResolution(
                transaction_type="Unknown",
                confidence_score=0,
                resolution_source="unknown",
                amount=eff_amount
            )
            
        unique_directions = set(signals.values())
        
        if len(unique_directions) > 1:
            # Conflicting signals
            return TypeResolution(
                transaction_type="Conflict",
                confidence_score=0,
                resolution_source="conflict",
                amount=eff_amount
            )
            
        final_type = unique_directions.pop()
        
        # 3. Compute Confidence and Source
        if len(signals) > 1:
            confidence = 100
            source = "multiple_signals"
        elif 'marker' in signals:
            confidence = 99
            source = "description_marker"
        elif 'balance' in signals:
            confidence = 98
            source = "balance_reconciliation"
        elif 'column' in signals:
            confidence = 95
            source = "statement_column"
        else:
            confidence = 90
            source = "inferred"
            
        return TypeResolution(
            transaction_type=final_type,
            confidence_score=confidence,
            resolution_source=source,
            amount=eff_amount
        )
