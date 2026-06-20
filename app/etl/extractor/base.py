"""
Abstract Base Extractor
All statement extractors must implement this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date


@dataclass
class RawTransaction:
    """Represents a single raw transaction as extracted from the source."""
    date: Optional[str] = None
    description: str = ''
    debit: Optional[str] = None
    credit: Optional[str] = None
    amount: Optional[str] = None
    balance: Optional[str] = None
    reference_no: Optional[str] = None
    raw_row: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StatementMetadata:
    """Metadata extracted from the statement header/footer."""
    institution: Optional[str] = None
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    statement_period_start: Optional[date] = None
    statement_period_end: Optional[date] = None
    currency: str = 'INR'
    raw_text: Optional[str] = None


@dataclass
class ExtractionResult:
    """Result of a full extraction pass on a statement."""
    metadata: StatementMetadata = field(default_factory=StatementMetadata)
    transactions: List[RawTransaction] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    success: bool = True


class BaseExtractor(ABC):
    """Abstract base class for all statement extractors."""

    def __init__(self):
        self.errors: List[str] = []

    @abstractmethod
    def can_handle(self, file_path: str) -> bool:
        """Return True if this extractor can handle the given file."""
        pass

    @abstractmethod
    def extract(self, file_path: str) -> ExtractionResult:
        """Extract raw transactions and metadata from the file."""
        pass

    def _log_error(self, message: str):
        self.errors.append(message)
