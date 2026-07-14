"""Wallet business rules."""

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.fastapi_app.models.transaction import Transaction
from app.fastapi_app.repositories.wallet_repository import WalletRepository
from app.fastapi_app.schemas.wallet import WalletCreate, WalletTransferResponse, WalletUpdate


class WalletService:
    allowed_types = {"Cash", "Bank", "UPI", "Credit", "Custom"}


    def __init__(self, session: Session) -> None:
        self.session = session
        self.wallets = WalletRepository(session)

    type_mapping = {
        "bank": "Bank",
        "cash": "Cash",
        "credit_card": "Credit",
        "digital": "UPI",
        "custom": "Custom"
    }

    def _normalize_type(self, wallet_type: str) -> str:
        val = wallet_type.strip()
        if val in self.allowed_types:
            return val
        norm = self.type_mapping.get(val.lower())
        if norm:
            return norm
        title_val = val.title()
        if title_val in self.allowed_types:
            return title_val
        return val

    def create_wallet(self, user_id: int, payload: WalletCreate):
        norm_type = self._normalize_type(payload.wallet_type)
        self._validate_type(norm_type)
        wallet = self.wallets.create(
            user_id=user_id,
            wallet_name=payload.wallet_name,
            wallet_type=norm_type,
            balance=payload.balance,
        )
        self.session.commit()
        self.session.refresh(wallet)
        return wallet

    def update_wallet(self, user_id: int, wallet_id: int, payload: WalletUpdate):
        wallet = self.wallets.get_owned(wallet_id, user_id)
        if not wallet:
            return None
        if payload.wallet_name is not None:
            wallet.wallet_name = payload.wallet_name.strip()
        if payload.wallet_type is not None:
            norm_type = self._normalize_type(payload.wallet_type)
            self._validate_type(norm_type)
            wallet.wallet_type = norm_type
        if payload.balance is not None:
            wallet.balance = payload.balance
        self.session.commit()
        self.session.refresh(wallet)
        return wallet

    def delete_wallet(self, user_id: int, wallet_id: int) -> bool:
        wallet = self.wallets.get_owned(wallet_id, user_id)
        if not wallet:
            return False
        self.wallets.delete(wallet)
        self.session.commit()
        return True

    def list_wallets(self, user_id: int, include_archived: bool = False):
        return self.wallets.list_by_user(user_id, include_archived=include_archived)

    def wallet_summary(self, user_id: int):
        return self.wallets.summary(user_id)

    def archive_wallet(self, user_id: int, wallet_id: int) -> bool:
        wallet = self.wallets.get_owned(wallet_id, user_id)
        if not wallet:
            return False
        self.wallets.archive(wallet)
        self.session.commit()
        return True

    def transfer(self, user_id: int, from_wallet_id: int, to_wallet_id: int, amount: float, notes: Optional[str], transaction_date: Optional[str]) -> WalletTransferResponse:
        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")
        if from_wallet_id == to_wallet_id:
            raise ValueError("Cannot transfer to the same wallet.")
        
        from_wallet = self.wallets.get_owned(from_wallet_id, user_id)
        to_wallet = self.wallets.get_owned(to_wallet_id, user_id)
        if not from_wallet or not to_wallet:
            raise ValueError("One or both wallets not found.")

        try:
            t_date = date.fromisoformat(transaction_date) if transaction_date else date.today()
        except Exception:
            t_date = date.today()
        
        # Create debit transaction
        debit_txn = Transaction(
            user_id=user_id,
            wallet_id=from_wallet_id,
            merchant_name=f"Transfer to {to_wallet.wallet_name}",
            category="Transfers",
            amount=amount,
            transaction_type="Expense",
            notes=notes,
            transaction_date=t_date,
            is_transfer=True
        )
        self.session.add(debit_txn)
        self.session.flush()
        
        # Create credit transaction
        credit_txn = Transaction(
            user_id=user_id,
            wallet_id=to_wallet_id,
            merchant_name=f"Transfer from {from_wallet.wallet_name}",
            category="Transfers",
            amount=amount,
            transaction_type="Income",
            notes=notes,
            transaction_date=t_date,
            is_transfer=True,
            transfer_pair_id=debit_txn.id
        )
        self.session.add(credit_txn)
        self.session.flush()
        
        # Link debit to credit (circular link)
        debit_txn.transfer_pair_id = credit_txn.id
        
        # Update balances
        from_wallet.balance = float(from_wallet.balance or 0) - amount
        to_wallet.balance = float(to_wallet.balance or 0) + amount
        
        self.session.commit()
        self.session.refresh(debit_txn)
        self.session.refresh(credit_txn)

        return WalletTransferResponse(
            debit_transaction_id=debit_txn.id,
            credit_transaction_id=credit_txn.id,
            amount=amount,
            from_wallet_balance=float(from_wallet.balance),
            to_wallet_balance=float(to_wallet.balance)
        )

    def _validate_type(self, wallet_type: str) -> None:
        if wallet_type not in self.allowed_types:
            raise ValueError(f"Invalid wallet type. Allowed values: {', '.join(sorted(self.allowed_types))}")
