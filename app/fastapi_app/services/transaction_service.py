"""Transaction business rules."""

from sqlalchemy.orm import Session

from app.fastapi_app.repositories.transaction_repository import TransactionRepository
from app.fastapi_app.repositories.wallet_repository import WalletRepository
from app.fastapi_app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:
    allowed_types = {"Income", "Expense"}

    def __init__(self, session: Session) -> None:
        self.session = session
        self.transactions = TransactionRepository(session)
        self.wallets = WalletRepository(session)

    def create_transaction(self, user_id: int, payload: TransactionCreate):
        self._validate_type(payload.transaction_type)
        wallet = self.wallets.get_owned(payload.wallet_id, user_id)
        if not wallet:
            raise ValueError("Wallet not found for this user.")

        transaction = self.transactions.create(
            user_id=user_id,
            wallet_id=payload.wallet_id,
            merchant_name=payload.merchant_name.strip(),
            category=payload.category.strip() if payload.category else None,
            amount=payload.amount,
            transaction_type=payload.transaction_type,
            notes=payload.notes.strip() if payload.notes else None,
            transaction_date=payload.transaction_date,
        )
        self._apply_wallet_balance(wallet, payload.amount, payload.transaction_type)
        self.session.commit()
        self.session.refresh(transaction)
        return transaction

    def update_transaction(self, user_id: int, transaction_id: int, payload: TransactionUpdate):
        transaction = self.transactions.get_owned(transaction_id, user_id)
        if not transaction:
            return None

        previous_wallet = self.wallets.get_owned(transaction.wallet_id, user_id)
        previous_amount = float(transaction.amount)
        previous_type = transaction.transaction_type

        if payload.wallet_id is not None:
            wallet = self.wallets.get_owned(payload.wallet_id, user_id)
            if not wallet:
                raise ValueError("Wallet not found for this user.")
            transaction.wallet_id = payload.wallet_id
        if payload.merchant_name is not None:
            transaction.merchant_name = payload.merchant_name.strip()
        if payload.category is not None:
            transaction.category = payload.category.strip() if payload.category else None
        if payload.amount is not None:
            transaction.amount = payload.amount
        if payload.transaction_type is not None:
            self._validate_type(payload.transaction_type)
            transaction.transaction_type = payload.transaction_type
        if payload.notes is not None:
            transaction.notes = payload.notes.strip() if payload.notes else None
        if payload.transaction_date is not None:
            transaction.transaction_date = payload.transaction_date

        if previous_wallet:
            self._apply_wallet_balance(previous_wallet, previous_amount, self._reverse_type(previous_type))
        current_wallet = self.wallets.get_owned(transaction.wallet_id, user_id)
        if current_wallet:
            self._apply_wallet_balance(current_wallet, float(transaction.amount), transaction.transaction_type)

        self.session.commit()
        self.session.refresh(transaction)
        return transaction

    def delete_transaction(self, user_id: int, transaction_id: int) -> bool:
        transaction = self.transactions.get_owned(transaction_id, user_id)
        if not transaction:
            return False
        wallet = self.wallets.get_owned(transaction.wallet_id, user_id)
        if wallet:
            self._apply_wallet_balance(wallet, float(transaction.amount), self._reverse_type(transaction.transaction_type))
        self.transactions.delete(transaction)
        self.session.commit()
        return True

    def list_transactions(self, user_id: int, **filters):
        return self.transactions.list_filtered(user_id=user_id, **filters)

    def _validate_type(self, transaction_type: str) -> None:
        if transaction_type not in self.allowed_types:
            raise ValueError(f"Invalid transaction type. Allowed values: {', '.join(sorted(self.allowed_types))}")

    def _reverse_type(self, transaction_type: str) -> str:
        return "Expense" if transaction_type == "Income" else "Income"

    def _apply_wallet_balance(self, wallet, amount: float, transaction_type: str) -> None:
        if transaction_type == "Income":
            wallet.balance = float(wallet.balance or 0) + amount
        else:
            wallet.balance = float(wallet.balance or 0) - amount
