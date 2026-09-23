import sys
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, '.')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.fastapi_app.db.base import Base
from app.fastapi_app.models.user import User
from app.fastapi_app.models.wallet import Wallet
from app.fastapi_app.models.transaction import Transaction
from app.fastapi_app.services.advisor_context_service import AdvisorContextService
from app.fastapi_app.services.dashboard_service import DashboardService

def setup_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    
    user1 = User(id=1, full_name="User One", email="test1@test.com", password_hash="hash")
    user2 = User(id=2, full_name="User Two", email="test2@test.com", password_hash="hash")
    db.add(user1)
    db.add(user2)
    db.commit()
    
    w1 = Wallet(id=1, user_id=1, wallet_name="Bank", wallet_type="Bank")
    w2 = Wallet(id=2, user_id=2, wallet_name="Bank", wallet_type="Bank")
    db.add(w1)
    db.add(w2)
    db.commit()
    return db

def test_financial_context_aggregation():
    db = setup_db()
    today = date.today()
    prev_month = date(today.year, today.month, 1) - timedelta(days=5)
    
    # 1. Income
    t1 = Transaction(user_id=1, wallet_id=1, merchant_name="Salary", amount=5000, transaction_type="Income", transaction_date=today)
    # 2. Credit (from SBI)
    t2 = Transaction(user_id=1, wallet_id=1, merchant_name="UPI/CR", amount=2000, transaction_type="Credit", transaction_date=today)
    # 3. Expense
    t3 = Transaction(user_id=1, wallet_id=1, merchant_name="Food", amount=1500, transaction_type="Expense", transaction_date=today)
    # 4. Debit (from SBI)
    t4 = Transaction(user_id=1, wallet_id=1, merchant_name="UPI/DR", amount=500, transaction_type="Debit", transaction_date=today)
    # 5. Different User
    t5 = Transaction(user_id=2, wallet_id=2, merchant_name="OtherUser", amount=9999, transaction_type="Credit", transaction_date=today)
    # 6. Previous Month
    t6 = Transaction(user_id=1, wallet_id=1, merchant_name="Old", amount=1000, transaction_type="Income", transaction_date=prev_month)
    # 7. Transfer (should be excluded if is_transfer=True)
    t7 = Transaction(user_id=1, wallet_id=1, merchant_name="Self", amount=1000, transaction_type="Expense", transaction_date=today, is_transfer=True)
    
    db.add_all([t1, t2, t3, t4, t5, t6, t7])
    db.commit()
    
    adv = AdvisorContextService(db)
    ctx = adv.get_context(1)
    
    # A. If September has qualifying Credit/Income transactions: monthly_income > 0
    # Expected Income = 5000 (Income) + 2000 (Credit) = 7000
    assert ctx["monthly_income"] == 7000.0
    
    # Expected Expense = 1500 (Expense) + 500 (Debit) = 2000
    assert ctx["monthly_expense"] == 2000.0
    
    # D. monthly_savings = monthly_income - monthly_expense
    assert ctx["monthly_savings"] == 5000.0
    
    # E. "No Income Detected" is NOT generated when monthly_income > 0
    anomalies = [a["title"] for a in ctx["anomalies_and_insights"]]
    assert "No Income Detected" not in anomalies
    
    # Check historical trends for current month
    trends = ctx["historical_trends"]
    current_trend = trends[-1]
    assert current_trend["month"] == f"{today.year}-{today.month:02d}"
    assert current_trend["income"] == 7000.0
    assert current_trend["expense"] == 2000.0
    
    # G. Previous months remain correctly calculated
    prev_trend = trends[-2]
    assert prev_trend["income"] == 1000.0

def test_anomaly_zero_income():
    db = setup_db()
    today = date.today()
    
    # No income, only expense
    t1 = Transaction(user_id=1, wallet_id=1, merchant_name="Food", amount=1500, transaction_type="Expense", transaction_date=today)
    db.add(t1)
    db.commit()
    
    adv = AdvisorContextService(db)
    ctx = adv.get_context(1)
    
    assert ctx["monthly_income"] == 0.0
    assert ctx["monthly_expense"] == 1500.0
    
    anomalies = [a["title"] for a in ctx["anomalies_and_insights"]]
    assert "No Income Detected" in anomalies

if __name__ == "__main__":
    test_financial_context_aggregation()
    test_anomaly_zero_income()
    print("All regression tests passed.")
