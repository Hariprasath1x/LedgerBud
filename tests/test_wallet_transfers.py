"""Test wallet services — transfer and archive functionality."""

import pytest
from app.fastapi_app.services.wallet_service import WalletService
from app.fastapi_app.schemas.wallet import WalletCreate


def test_wallet_creation_and_archiving(db_session):
    service = WalletService(db_session)
    
    # 1. Create a wallet
    wallet = service.create_wallet(
        user_id=1,
        payload=WalletCreate(wallet_name="Test Wallet", wallet_type="Bank", balance=1000.0)
    )
    
    assert wallet.id is not None
    assert wallet.wallet_name == "Test Wallet"
    assert wallet.is_archived is False
    
    # 2. Archive the wallet
    success = service.archive_wallet(user_id=1, wallet_id=wallet.id)
    assert success is True
    
    # Wallet should not be returned in default list
    wallets = service.list_wallets(user_id=1, include_archived=False)
    assert len(wallets) == 0
    
    # Wallet should be returned when include_archived is True
    wallets_all = service.list_wallets(user_id=1, include_archived=True)
    assert len(wallets_all) == 1
    assert wallets_all[0].is_archived is True


def test_atomic_transfer(db_session):
    service = WalletService(db_session)
    
    # Create two wallets
    w1 = service.create_wallet(user_id=1, payload=WalletCreate(wallet_name="W1", wallet_type="Bank", balance=500.0))
    w2 = service.create_wallet(user_id=1, payload=WalletCreate(wallet_name="W2", wallet_type="Cash", balance=100.0))
    
    # Perform transfer
    res = service.transfer(
        user_id=1,
        from_wallet_id=w1.id,
        to_wallet_id=w2.id,
        amount=150.0,
        notes="Testing transfer",
        transaction_date="2026-07-13"
    )
    
    assert res.amount == 150.0
    assert res.from_wallet_balance == 350.0
    assert res.to_wallet_balance == 250.0
    
    # Verify transaction links
    from app.fastapi_app.models.transaction import Transaction
    from sqlalchemy import select
    
    txns = db_session.scalars(select(Transaction).where(Transaction.user_id == 1)).all()
    assert len(txns) == 2
    
    debit_txn = next(t for t in txns if t.transaction_type == "Expense")
    credit_txn = next(t for t in txns if t.transaction_type == "Income")
    
    assert debit_txn.amount == 150.0
    assert debit_txn.is_transfer is True
    assert debit_txn.transfer_pair_id == credit_txn.id
    
    assert credit_txn.amount == 150.0
    assert credit_txn.is_transfer is True
    assert credit_txn.transfer_pair_id == debit_txn.id
