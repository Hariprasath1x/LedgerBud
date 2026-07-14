"""Transaction persistence operations."""

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.fastapi_app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, **data) -> Transaction:
        transaction = Transaction(**data)
        self.session.add(transaction)
        self.session.flush()
        return transaction

    def get_owned(self, transaction_id: int, user_id: int) -> Transaction | None:
        statement = select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id)
        return self.session.scalar(statement)

    def list_filtered(
        self,
        *,
        user_id: int,
        wallet_id: int | None = None,
        search: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        is_transfer: bool | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Transaction], int]:
        statement = select(Transaction).where(Transaction.user_id == user_id)
        if wallet_id:
            statement = statement.where(Transaction.wallet_id == wallet_id)
        if category:
            statement = statement.where(Transaction.category == category)
        if transaction_type:
            statement = statement.where(Transaction.transaction_type == transaction_type)
        if search:
            statement = statement.where(Transaction.merchant_name.ilike(f"%{search}%"))
        if is_transfer is not None:
            if is_transfer:
                statement = statement.where(Transaction.is_transfer == True)
            else:
                from sqlalchemy import or_
                statement = statement.where(or_(Transaction.is_transfer == False, Transaction.is_transfer == None))

        count_statement = select(func.count()).select_from(statement.subquery())
        total = int(self.session.scalar(count_statement) or 0)
        statement = statement.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).offset((page - 1) * per_page).limit(per_page)
        return list(self.session.scalars(statement).all()), total

    def delete(self, transaction: Transaction) -> None:
        self.session.delete(transaction)
