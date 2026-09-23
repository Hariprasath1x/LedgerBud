import sys
from decimal import Decimal

sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from app.etl.extractor.base import RawTransaction
from app.fastapi_app.services.import_service import ImportService
from app.fastapi_app.models.user import User
from app.fastapi_app.models.wallet import Wallet
from app.fastapi_app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

user = db.query(User).filter(User.email=="test@ledgerbud.local").first()
wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()

raw_desc = (
    "10:06:18 Cheque No.:103812668091 "
    "07-Aug-2026 NACH MONTHLY CASH ASSISTA 8527459677860 "
    "UPI/CR/127536852728/C KAMATCHI/IBKL/**RAN60@OKHDFCBANK/UPI/... "
    "07-Aug-2026 ... "
    "UPI/DR/621979888177/SBIPMOPAD/SBIP/**70750@SBIPAY/... "
    "... "
    "UPI/CR/658673283261/G CHANDRA/... "
    "UPI/DR/622072649129/FLIPKART... "
    "... "
    "UPI/CR/658665497859/G CHANDRA... "
    "..."
)

# If PDF extractor extracted these as separate rows with amounts:
# Since they are wrapped, we'll simulate the table extractor properly splitting them by is_clash
# or the segmenter splitting them if they lacked amounts. We'll pass them in as individual RawTransactions
# as if the extractor parsed them, or just use the pipeline with CSV.
# Wait, let's use the actual pipeline with a CSV where the extractor outputs them:
csv_data = (
    "date,description,amount,balance\n"
    "2026-08-07,NACH MONTHLY CASH ASSISTA 8527459677860,1000.00,1000.64\n"
    "2026-08-07,UPI/CR/127536852728/C KAMATCHI,500.00,1500.64\n"
    "2026-08-07,UPI/DR/621979888177/SBIPMOPAD,200.00,1300.64\n"
    "2026-08-07,UPI/CR/658673283261/G CHANDRA,300.00,1600.64\n"
    "2026-08-08,UPI/DR/622072649129/FLIPKART,100.00,1500.64\n"
    "2026-08-08,UPI/CR/658665497859/G CHANDRA,400.00,1900.64\n"
).encode()

svc = ImportService(db)
preview = svc.process_upload(user.id, wallet.id, csv_data, "sample.csv")

print("DIAGNOSTIC TABLE")
print(f"{'Idx':<4} | {'Date':<10} | {'Type':<8} | {'Amount':<8} | {'Status':<10} | {'Review':<6} | {'Merchant':<15} | {'Description'}")
print("-" * 120)

for idx, rec in enumerate(preview.transactions):
    print(f"{idx:<4} | {rec.date:<10} | {rec.transaction_type:<8} | {str(rec.amount):<8} | {rec.financial_data_status:<10} | {str(rec.requires_review):<6} | {rec.merchant_name[:15]:<15} | {rec.description[:40]}")

print("\n--- VALIDATION ---")
for txn in preview.transactions:
    if txn.requires_review:
        assert txn.amount is None or txn.amount <= 0, "Review required but amount > 0"
        assert txn.financial_data_status == "incomplete", "Review required but status complete"
    else:
        assert txn.amount > 0, f"Valid transaction has invalid amount: {txn.amount}"
        assert txn.transaction_type in ["Credit", "Debit", "Unknown", "Conflict"], f"Invalid type: {txn.transaction_type}"
        assert txn.date, "Missing date"

print("All integrity checks passed.")
