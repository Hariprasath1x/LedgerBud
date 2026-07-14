"""Create wallets and transactions tables.

Revision ID: 0002_create_wallets_and_transactions
Revises: 0001_create_users_table
Create Date: 2026-06-20 00:00:00.000001
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_create_wallets_and_transactions"
down_revision = "0001_create_users_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wallets",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("wallet_name", sa.String(length=120), nullable=False),
        sa.Column("wallet_type", sa.String(length=30), nullable=False),
        sa.Column("balance", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_wallets_user_id", "wallets", ["user_id"], unique=False)
    op.create_index("ix_wallets_id", "wallets", ["id"], unique=False)

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=False),
        sa.Column("merchant_name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"], unique=False)
    op.create_index("ix_transactions_wallet_id", "transactions", ["wallet_id"], unique=False)
    op.create_index("ix_transactions_transaction_date", "transactions", ["transaction_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_transactions_transaction_date", table_name="transactions")
    op.drop_index("ix_transactions_wallet_id", table_name="transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_table("transactions")

    op.drop_index("ix_wallets_id", table_name="wallets")
    op.drop_index("ix_wallets_user_id", table_name="wallets")
    op.drop_table("wallets")