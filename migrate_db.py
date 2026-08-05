import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.fastapi_app.db.session import engine
from app.fastapi_app.db.base import Base
from app.fastapi_app.models import User, Wallet, Transaction, Budget, Goal, Subscription, ImportJob, NetWorthItem, NetWorthSnapshot, FireAnalysis, Merchant

def run_migration():
    print("Creating all tables via Base.metadata.create_all...")
    Base.metadata.create_all(bind=engine)
    
    print("Altering transactions table to add new columns...")
    queries = [
        "ALTER TABLE transactions ADD COLUMN merchant_id INTEGER NULL;",
        "ALTER TABLE transactions ADD CONSTRAINT fk_transactions_merchant_id FOREIGN KEY (merchant_id) REFERENCES merchants (id) ON DELETE SET NULL;",
        "ALTER TABLE transactions ADD COLUMN raw_description TEXT NULL;",
        "ALTER TABLE transactions ADD COLUMN normalized_description TEXT NULL;",
        "ALTER TABLE transactions ADD COLUMN confidence_score INTEGER NULL;",
        "ALTER TABLE transactions ADD COLUMN recognition_source VARCHAR(100) NULL;",
        "ALTER TABLE transactions ADD COLUMN matching_method VARCHAR(100) NULL;",
        "ALTER TABLE transactions ADD COLUMN reason_for_decision TEXT NULL;"
    ]
    
    with engine.begin() as conn:
        for q in queries:
            try:
                conn.execute(text(q))
                print(f"Executed: {q}")
            except Exception as e:
                print(f"Skipped (likely already exists): {e}")

if __name__ == "__main__":
    run_migration()
