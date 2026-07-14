"""Test Advisor Context Aggregation service."""

import pytest
from datetime import date
from app.fastapi_app.services.advisor_context_service import AdvisorContextService
from app.fastapi_app.services.wallet_service import WalletService
from app.fastapi_app.services.transaction_service import TransactionService
from app.fastapi_app.schemas.wallet import WalletCreate
from app.fastapi_app.schemas.transaction import TransactionCreate
from app.fastapi_app.services.net_worth_service import NetWorthService
from app.fastapi_app.schemas.net_worth import NetWorthItemCreate


def test_advisor_context_compilation(db_session):
    wallet_svc = WalletService(db_session)
    txn_svc = TransactionService(db_session)
    nw_svc = NetWorthService(db_session)
    
    # 1. Create a wallet and record some transactions
    wallet = wallet_svc.create_wallet(user_id=1, payload=WalletCreate(wallet_name="Checking", wallet_type="Bank", balance=2000.0))
    
    # Add income
    txn_svc.create_transaction(
        user_id=1,
        payload=TransactionCreate(
            wallet_id=wallet.id,
            merchant_name="Salary",
            category="Salary",
            amount=5000.0,
            transaction_type="Income",
            transaction_date=date.today()
        )
    )
    
    # Add expense
    txn_svc.create_transaction(
        user_id=1,
        payload=TransactionCreate(
            wallet_id=wallet.id,
            merchant_name="Restaurant",
            category="Food & Dining",
            amount=1500.0,
            transaction_type="Expense",
            transaction_date=date.today()
        )
    )
    
    # 2. Add Net Worth items
    nw_svc.create_item(
        user_id=1,
        payload=NetWorthItemCreate(
            name="Savings Account",
            item_type="asset",
            category="Cash & Savings",
            amount=10000.0
        )
    )
    
    # Compile context
    context_svc = AdvisorContextService(db_session)
    context = context_svc.get_context(user_id=1)
    
    assert context["wallet_balance"] == 5500.0  # 2000 + 5000 - 1500
    assert context["net_worth"] == 10000.0
    assert context["monthly_income"] == 5000.0
    assert context["monthly_expense"] == 1500.0
    assert context["monthly_savings"] == 3500.0
    assert context["savings_rate_percent"] == 70.0
    assert len(context["top_categories"]) == 1
    assert context["top_categories"][0]["category"] == "Food & Dining"
