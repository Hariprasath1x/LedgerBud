import sys
import os
import json
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.fastapi_app.services.import_service import ImportService
from app.fastapi_app.models.user import User
from app.fastapi_app.models.wallet import Wallet
from app.fastapi_app.core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

user = db.query(User).filter(User.email=="test@ledgerbud.local").first()
if not user:
    user = User(email="test@ledgerbud.local", firebase_uid="test_uid", full_name="Test")
    db.add(user)
    db.commit()
    db.refresh(user)

wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
if not wallet:
    wallet = Wallet(user_id=user.id, wallet_name="Test Wallet", wallet_type="Checking", balance=0)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)

# Simulate the EXACT string from the user prompt
raw_desc = (
    "10:06:18 Cheque No.:103812668091 "
    "07-Aug-2026 NACH MONTHLY CASH ASSISTA 8527459677860 "
    "UPI/CR/127536852728/C KAMATCHI/IBKL/**RAN60@OKHDFCBANK/UPI/... "
    "07-Aug-2026 ... "
    "UPI/DR/621979888177/SBIPMOPAD/SBIP/**70750@SBIPAY/... "
    "... "
    "UPI/DR/123/FLIPKART... "
    "... "
    "UPI/CR/456/G CHANDRA... "
    "..."
)

# This was the single row extracted from the PDF
csv_data = b"date,description,amount,balance\n2026-08-07," + raw_desc.encode() + b",1000.00,1000.64\n"

svc = ImportService(db)
preview = svc.process_upload(user.id, wallet.id, csv_data, "sample.csv")

print(f"Total Transactions: {len(preview.transactions)}\n")

for rec in preview.transactions:
    print(f"[{rec.type_source}] Type: {rec.transaction_type} ({rec.type_confidence}%)")
    print(f"[{rec.merchant_source}] Merchant: {rec.merchant_name} ({rec.merchant_confidence}%)")
    print(f"Description: {rec.description}")
    print(f"Amount: {rec.amount}")
    print("-" * 50)
