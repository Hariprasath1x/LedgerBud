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
from app.fastapi_app.services.dashboard_service import DashboardService
from app.fastapi_app.services.advisor_context_service import AdvisorContextService

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Find the user with the 2100 expense
target_user = None
for u in db.query(User).all():
    txns = db.query(Transaction).filter(
        Transaction.user_id == u.id,
        Transaction.transaction_date >= date(2026, 9, 1),
        Transaction.transaction_date <= date(2026, 9, 30),
        Transaction.transaction_type == "Expense"
    ).all()
    valid_txns = [t for t in txns if not t.is_transfer]
    if sum(float(t.amount) for t in valid_txns) == 2100:
        target_user = u
        break

if not target_user:
    print("Could not find user with 2100 September expenses.")
    sys.exit(1)

user_id = target_user.id
print(f"Target user ID: {user_id}")

txns = db.query(Transaction).filter(
    Transaction.user_id == user_id,
    Transaction.transaction_date >= date(2026, 8, 1),
    Transaction.transaction_date <= date(2026, 9, 30)
).order_by(Transaction.transaction_date).all()

aug_txns = [t for t in txns if t.transaction_date.month == 8]
sep_txns = [t for t in txns if t.transaction_date.month == 9]

print("\nA. Raw DB September transactions")
for t in sep_txns:
    print(f"ID: {t.id} | Date: {t.transaction_date} | Desc: {t.merchant_name} | Amt: {t.amount} | Type: {t.transaction_type} | Cat: {t.category} | Wallet: {t.wallet_id} | Transfer: {t.is_transfer}")

print("\nB. Raw DB August transactions")
for t in aug_txns:
    print(f"ID: {t.id} | Date: {t.transaction_date} | Desc: {t.merchant_name} | Amt: {t.amount} | Type: {t.transaction_type} | Cat: {t.category} | Wallet: {t.wallet_id} | Transfer: {t.is_transfer}")

def calc_totals(txn_list):
    res = {"Credit": 0.0, "Debit": 0.0, "Income": 0.0, "Expense": 0.0}
    for t in txn_list:
        if t.is_transfer:
            continue
        if t.transaction_type in res:
            res[t.transaction_type] += float(t.amount)
    res["AggIncome"] = res["Income"] + res["Credit"]
    res["AggExpense"] = res["Expense"] + res["Debit"]
    return res

sep_totals = calc_totals(sep_txns)
aug_totals = calc_totals(aug_txns)

print("\nC. September income calculation")
print(f"Income: {sep_totals['Income']} | Credit: {sep_totals['Credit']} -> Total Aggregated: {sep_totals['AggIncome']}")

print("\nD. September expense calculation")
print(f"Expense: {sep_totals['Expense']} | Debit: {sep_totals['Debit']} -> Total Aggregated: {sep_totals['AggExpense']}")

print("\nE. August income calculation")
print(f"Income: {aug_totals['Income']} | Credit: {aug_totals['Credit']} -> Total Aggregated: {aug_totals['AggIncome']}")

print("\nF. August expense calculation")
print(f"Expense: {aug_totals['Expense']} | Debit: {aug_totals['Debit']} -> Total Aggregated: {aug_totals['AggExpense']}")

dash_svc = DashboardService(db)
dash_sum = dash_svc.get_summary(user_id)
trends = dash_svc.get_monthly_trends(user_id, months=3)
aug_trend = next((t for t in trends if t.month == "2026-08"), None)
sep_trend = next((t for t in trends if t.month == "2026-09"), None)

print("\nG. Whether DashboardService matches the DB")
print(f"DB Sept AggIncome: {sep_totals['AggIncome']} | Dashboard total_income: {dash_sum.total_income}")
print(f"DB Sept AggExpense: {sep_totals['AggExpense']} | Dashboard total_expense: {dash_sum.total_expense}")
print(f"DB Aug AggIncome: {aug_totals['AggIncome']} | Dashboard Aug Trend Income: {aug_trend.income if aug_trend else None}")
print(f"DB Aug AggExpense: {aug_totals['AggExpense']} | Dashboard Aug Trend Expense: {aug_trend.expense if aug_trend else None}")

adv_svc = AdvisorContextService(db)
ctx = adv_svc.get_context(user_id)

print("\nH. Whether AI Context matches DashboardService")
print(f"AI Context monthly_income: {ctx['monthly_income']} | Dashboard total_income: {dash_sum.total_income}")
print(f"AI Context monthly_expense: {ctx['monthly_expense']} | Dashboard total_expense: {dash_sum.total_expense}")
print(f"AI Context historical_trends Aug Income: {[t['income'] for t in ctx['historical_trends'] if '2026-08' in t['month']][0]}")
print(f"AI Context historical_trends Sept Income: {[t['income'] for t in ctx['historical_trends'] if '2026-09' in t['month']][0]}")

print("\nI. Exact source of the ₹2100 September expense")
for t in sep_txns:
    if t.transaction_type == "Expense" and not t.is_transfer:
        print(f"ID: {t.id} | Amt: {t.amount} | Desc: {t.merchant_name}")

print("\nJ. Any remaining inconsistency")
if (dash_sum.total_income == sep_totals['AggIncome'] and 
    dash_sum.total_expense == sep_totals['AggExpense'] and
    ctx['monthly_income'] == dash_sum.total_income and
    ctx['monthly_expense'] == dash_sum.total_expense):
    print("DATA FLOW VERIFIED — NO CODE CHANGE REQUIRED.")
else:
    print("MISMATCH DETECTED!")
