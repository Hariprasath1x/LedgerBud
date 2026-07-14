"""Wallet persistence operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.fastapi_app.models.transaction import Transaction
from app.fastapi_app.models.wallet import Wallet


class WalletRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_user(self, user_id: int, include_archived: bool = False) -> list[Wallet]:
        statement = select(Wallet).where(Wallet.user_id == user_id)
        if not include_archived:
            statement = statement.where(Wallet.is_archived == False)
        statement = statement.order_by(Wallet.created_at.desc())
        return list(self.session.scalars(statement).all())

    def get_owned(self, wallet_id: int, user_id: int) -> Wallet | None:
        statement = select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id)
        return self.session.scalar(statement)

    def create(self, *, user_id: int, wallet_name: str, wallet_type: str, balance: float) -> Wallet:
        wallet = Wallet(user_id=user_id, wallet_name=wallet_name.strip(), wallet_type=wallet_type.strip(), balance=balance)
        self.session.add(wallet)
        self.session.flush()
        return wallet

    def delete(self, wallet: Wallet) -> None:
        self.session.delete(wallet)

    def archive(self, wallet: Wallet) -> None:
        wallet.is_archived = True
        self.session.flush()

    def summary(self, user_id: int) -> dict[str, object]:
        wallets = self.list_by_user(user_id, include_archived=False)
        by_type: dict[str, float] = {}
        for wallet in wallets:
            by_type[wallet.wallet_type] = by_type.get(wallet.wallet_type, 0.0) + float(wallet.balance or 0)
        total_balance = float(sum(float(wallet.balance or 0) for wallet in wallets))
        return {
            "total_wallets": len(wallets),
            "total_balance": total_balance,
            "by_type": by_type,
        }
