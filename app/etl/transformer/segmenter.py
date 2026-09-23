import re
from typing import List
from app.etl.extractor.base import RawTransaction

def segment_transactions(transactions: List[RawTransaction]) -> List[RawTransaction]:
    """
    Refines row boundaries by splitting transactions that contain multiple
    transaction markers within a single description string.
    """
    segmented = []
    
    # Split by UPI/CR/ or UPI/DR/ but keep the delimiter attached to the right side
    # e.g. "foo UPI/CR/ bar" -> ["foo ", "UPI/CR/ bar"]
    marker_pattern = re.compile(r'(?=\bUPI/(?:CR|DR)/)', re.IGNORECASE)
    
    for txn in transactions:
        desc = txn.description or ""
        parts = marker_pattern.split(desc)
        
        # Clean parts and keep only non-empty
        parts = [p.strip() for p in parts if p.strip()]
        
        if not parts:
            segmented.append(txn)
            continue
            
        # The first part inherits all financial data from the original txn
        first_txn = RawTransaction(
            date=txn.date,
            description=parts[0],
            debit=txn.debit,
            credit=txn.credit,
            amount=txn.amount,
            balance=txn.balance,
            reference_no=txn.reference_no,
            raw_row=txn.raw_row
        )
        segmented.append(first_txn)
        
        # Subsequent parts are new transactions that share the same date
        # They do not inherit the amount/balance to prevent silent data corruption
        for part in parts[1:]:
            new_txn = RawTransaction(
                date=txn.date,
                description=part,
                debit=None,
                credit=None,
                amount=None,
                balance=None,
                reference_no=None,
            )
            segmented.append(new_txn)
            
    return segmented
