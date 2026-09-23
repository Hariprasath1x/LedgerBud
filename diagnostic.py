import sys
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from app.fastapi_app.core.config import settings
from app.fastapi_app.models.transaction import Transaction
from app.fastapi_app.models.user import User

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

user = db.query(User).filter(User.email == "test@ledgerbud.local").first()
if not user:
    # Get first available user if test@ledgerbud.local is not present
    user = db.query(User).first()

if not user:
    print("No users found.")
    sys.exit(0)

print(f"Diagnostics for user: {user.email} (ID: {user.id})")

txns = db.query(Transaction).order_by(Transaction.transaction_date).all()

print("ALL TRANSACTIONS (Aug - Sept 2026)")
print(f"{'ID':<4} | {'Txn Date':<10} | {'Created At':<19} | {'Amount':<8} | {'Type':<8} | {'Merchant':<15} | {'Raw Desc'}")
print("-" * 120)

aug_income = 0.0
aug_income_txns = []

for t in txns:
    # Print the table row
    print(f"{t.id:<4} | {str(t.transaction_date):<10} | {str(t.created_at)[:19]:<19} | {float(t.amount):<8.2f} | {t.transaction_type:<8} | {str(t.merchant_name)[:15]:<15} | {str(t.raw_description)[:30]}")
    
    # Track August Income / Credit
    if t.transaction_date.month == 8 and t.transaction_type in ["Income", "Credit"]:
        aug_income += float(t.amount)
        aug_income_txns.append(t)

print("\n" + "=" * 50)
print(f"TRANSACTIONS CONTRIBUTING TO AUGUST INCOME ({aug_income})")
for t in aug_income_txns:
    print(f"ID: {t.id}, Date: {t.transaction_date}, Amount: {t.amount}, Type: {t.transaction_type}, Raw: {t.raw_description[:40]}")
    
print("\n" + "=" * 50)
print("DIAGNOSTIC SUMMARY")
print(f"Total August Income calculated from DB: {aug_income}")
