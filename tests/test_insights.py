"""Test Insights Engine rule triggers."""

import pytest
from datetime import date
from app.fastapi_app.services.insights_service import InsightsService
from app.fastapi_app.services.wallet_service import WalletService
from app.fastapi_app.services.transaction_service import TransactionService
from app.fastapi_app.schemas.wallet import WalletCreate
from app.fastapi_app.schemas.transaction import TransactionCreate
from app.fastapi_app.schemas.budget import BudgetCreate
from app.fastapi_app.services.budget_service import BudgetService


def test_zero_income_trigger(db_session):
    # Setup: Create wallet and add expense but no income
    wallet_svc = WalletService(db_session)
    txn_svc = TransactionService(db_session)
    
    wallet = wallet_svc.create_wallet(user_id=1, payload=WalletCreate(wallet_name="Checking", wallet_type="Bank", balance=5000.0))
    
    txn_svc.create_transaction(
        user_id=1,
        payload=TransactionCreate(
            wallet_id=wallet.id,
            merchant_name="Supermarket",
            category="Groceries",
            amount=500.0,
            transaction_type="Expense",
            transaction_date=date.today()
        )
    )
    
    insights_svc = InsightsService(db_session)
    insights = insights_svc.generate_insights(user_id=1)
    
    # "No Income Detected" should fire because there are expenses but no income
    assert any(i.type == "zero_income" for i in insights)


def test_budget_exceeded_trigger(db_session):
    wallet_svc = WalletService(db_session)
    txn_svc = TransactionService(db_session)
    budget_svc = BudgetService(db_session)
    
    wallet = wallet_svc.create_wallet(user_id=1, payload=WalletCreate(wallet_name="Checking", wallet_type="Bank", balance=5000.0))
    
    # Create a small budget
    budget_svc.create_budget(
        user_id=1,
        payload=BudgetCreate(
            name="Groceries Budget",
            category="Groceries",
            amount=200.0,
            period="monthly"
        )
    )
    
    # Spend more than budget
    txn_svc.create_transaction(
        user_id=1,
        payload=TransactionCreate(
            wallet_id=wallet.id,
            merchant_name="Store",
            category="Groceries",
            amount=250.0,
            transaction_type="Expense",
            transaction_date=date.today()
        )
    )
    
    insights_svc = InsightsService(db_session)
    insights = insights_svc.generate_insights(user_id=1)
    
    # "Budget Exceeded" should fire
    assert any(i.type == "budget_risk" and i.severity == "high" for i in insights)
