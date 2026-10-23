"""Complete PostgreSQL schema with all LedgerBud models.

Revision ID: c2905ef2a301
Revises: b1804dc1b57c
Create Date: 2026-10-23 12:00:00.000000

Adds:
- wallets: is_archived column
- merchants: full table for Financial Intelligence Pipeline
- transactions: transfer tracking and intelligence pipeline columns + foreign keys
- budgets: full table
- goals: full table
- subscriptions: full table
- import_jobs: full table
- net_worth_items: full table
- net_worth_snapshots: full table
- fire_analysis: full table
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2905ef2a301"
down_revision: Union[str, None] = "b1804dc1b57c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Ensure users.id has index matching model definition and boolean default is portable
    with op.batch_alter_table("users") as batch_op:
        batch_op.create_index(batch_op.f("ix_users_id"), ["id"], unique=False)
        batch_op.alter_column("is_active", existing_type=sa.Boolean(), server_default=sa.text("true"))

    # 1. Update wallets table: add is_archived column
    with op.batch_alter_table("wallets") as batch_op:
        batch_op.add_column(
            sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false"))
        )

    # 2. Create merchants table (referenced by transactions)
    op.create_table(
        "merchants",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("unique_identifier", sa.String(length=200), nullable=True),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("preferred_name", sa.String(length=200), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("user_confirmation_status", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("recognition_source", sa.String(length=100), nullable=True),
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.Column("total_transactions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0.00"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_merchants_id", "merchants", ["id"], unique=False)
    op.create_index("ix_merchants_user_id", "merchants", ["user_id"], unique=False)
    op.create_index("ix_merchants_unique_identifier", "merchants", ["unique_identifier"], unique=False)

    # 3. Update transactions table: transfer tracking + intelligence fields + foreign keys
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.create_index(batch_op.f("ix_transactions_id"), ["id"], unique=False)
        batch_op.add_column(
            sa.Column("is_transfer", sa.Boolean(), nullable=True, server_default=sa.text("false"))
        )
        batch_op.add_column(sa.Column("transfer_pair_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("merchant_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("raw_description", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("normalized_description", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("confidence_score", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("recognition_source", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("matching_method", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("reason_for_decision", sa.Text(), nullable=True))

        batch_op.create_index(batch_op.f("ix_transactions_transfer_pair_id"), ["transfer_pair_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_transactions_merchant_id"), ["merchant_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_transactions_transfer_pair_id", "transactions", ["transfer_pair_id"], ["id"], ondelete="SET NULL"
        )
        batch_op.create_foreign_key(
            "fk_transactions_merchant_id", "merchants", ["merchant_id"], ["id"], ondelete="SET NULL"
        )

    # 4. Create budgets table
    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False, server_default="monthly"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_budgets_id", "budgets", ["id"], unique=False)
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"], unique=False)

    # 5. Create goals table
    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("current_amount", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_goals_id", "goals", ["id"], unique=False)
    op.create_index("ix_goals_user_id", "goals", ["user_id"], unique=False)

    # 6. Create subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("merchant_name", sa.String(length=200), nullable=True),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("frequency", sa.String(length=30), nullable=False, server_default="monthly"),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("last_detected", sa.Date(), nullable=True),
        sa.Column("next_expected", sa.Date(), nullable=True),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("detection_confidence", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_subscriptions_id", "subscriptions", ["id"], unique=False)
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"], unique=False)

    # 7. Create import_jobs table
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("institution_detected", sa.String(length=100), nullable=True),
        sa.Column("account_number_detected", sa.String(length=50), nullable=True),
        sa.Column("statement_period_start", sa.Date(), nullable=True),
        sa.Column("statement_period_end", sa.Date(), nullable=True),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("preview_data", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_import_jobs_id", "import_jobs", ["id"], unique=False)
    op.create_index("ix_import_jobs_user_id", "import_jobs", ["user_id"], unique=False)
    op.create_index("ix_import_jobs_wallet_id", "import_jobs", ["wallet_id"], unique=False)

    # 8. Create net_worth_items table
    op.create_table(
        "net_worth_items",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_net_worth_items_id", "net_worth_items", ["id"], unique=False)
    op.create_index("ix_net_worth_items_user_id", "net_worth_items", ["user_id"], unique=False)

    # 9. Create net_worth_snapshots table
    op.create_table(
        "net_worth_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_assets", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("total_liabilities", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("net_worth", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_net_worth_snapshots_id", "net_worth_snapshots", ["id"], unique=False)
    op.create_index("ix_net_worth_snapshots_user_id", "net_worth_snapshots", ["user_id"], unique=False)
    op.create_index("ix_net_worth_snapshots_snapshot_date", "net_worth_snapshots", ["snapshot_date"], unique=False)

    # 10. Create fire_analysis table
    op.create_table(
        "fire_analysis",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("current_age", sa.Integer(), nullable=False, server_default="25"),
        sa.Column("retirement_target_age", sa.Integer(), nullable=False, server_default="45"),
        sa.Column("investment_return", sa.Float(), nullable=False, server_default="12.0"),
        sa.Column("inflation_rate", sa.Float(), nullable=False, server_default="6.0"),
        sa.Column("lifestyle", sa.String(length=50), nullable=False, server_default="Moderate"),
        sa.Column("current_net_worth", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("annual_income", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("annual_expenses", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("annual_savings", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("savings_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("fire_target_corpus", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("fire_progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("fire_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("estimated_fire_age", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("years_remaining", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("required_monthly_investment", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("wealth_projection", sa.JSON(), nullable=True),
        sa.Column("scenarios", sa.JSON(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=True),
        sa.Column("weaknesses", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_fire_analysis_id", "fire_analysis", ["id"], unique=False)
    op.create_index("ix_fire_analysis_user_id", "fire_analysis", ["user_id"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_index("ix_fire_analysis_user_id", table_name="fire_analysis")
    op.drop_index("ix_fire_analysis_id", table_name="fire_analysis")
    op.drop_table("fire_analysis")

    op.drop_index("ix_net_worth_snapshots_snapshot_date", table_name="net_worth_snapshots")
    op.drop_index("ix_net_worth_snapshots_user_id", table_name="net_worth_snapshots")
    op.drop_index("ix_net_worth_snapshots_id", table_name="net_worth_snapshots")
    op.drop_table("net_worth_snapshots")

    op.drop_index("ix_net_worth_items_user_id", table_name="net_worth_items")
    op.drop_index("ix_net_worth_items_id", table_name="net_worth_items")
    op.drop_table("net_worth_items")

    op.drop_index("ix_import_jobs_wallet_id", table_name="import_jobs")
    op.drop_index("ix_import_jobs_user_id", table_name="import_jobs")
    op.drop_index("ix_import_jobs_id", table_name="import_jobs")
    op.drop_table("import_jobs")

    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_id", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index("ix_goals_user_id", table_name="goals")
    op.drop_index("ix_goals_id", table_name="goals")
    op.drop_table("goals")

    op.drop_index("ix_budgets_user_id", table_name="budgets")
    op.drop_index("ix_budgets_id", table_name="budgets")
    op.drop_table("budgets")

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_constraint("fk_transactions_merchant_id", type_="foreignkey")
        batch_op.drop_constraint("fk_transactions_transfer_pair_id", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_transactions_merchant_id"))
        batch_op.drop_index(batch_op.f("ix_transactions_transfer_pair_id"))
        batch_op.drop_index(batch_op.f("ix_transactions_id"))
        batch_op.drop_column("reason_for_decision")
        batch_op.drop_column("matching_method")
        batch_op.drop_column("recognition_source")
        batch_op.drop_column("confidence_score")
        batch_op.drop_column("normalized_description")
        batch_op.drop_column("raw_description")
        batch_op.drop_column("merchant_id")
        batch_op.drop_column("transfer_pair_id")
        batch_op.drop_column("is_transfer")

    op.drop_index("ix_merchants_unique_identifier", table_name="merchants")
    op.drop_index("ix_merchants_user_id", table_name="merchants")
    op.drop_index("ix_merchants_id", table_name="merchants")
    op.drop_table("merchants")

    with op.batch_alter_table("wallets") as batch_op:
        batch_op.drop_column("is_archived")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_id"))
