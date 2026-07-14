"""Test Net Worth Tracker CRUD and historical snapshots."""

import pytest
from datetime import date
from app.fastapi_app.services.net_worth_service import NetWorthService
from app.fastapi_app.schemas.net_worth import NetWorthItemCreate, NetWorthItemUpdate


def test_net_worth_lifecycle(db_session):
    service = NetWorthService(db_session)
    
    # 1. Create items
    item1 = service.create_item(
        user_id=1,
        payload=NetWorthItemCreate(
            name="Emergency Fund",
            item_type="asset",
            category="Cash & Savings",
            amount=50000.0,
            notes="Savings account"
        )
    )
    
    item2 = service.create_item(
        user_id=1,
        payload=NetWorthItemCreate(
            name="Personal Loan",
            item_type="liability",
            category="Personal Loan",
            amount=10000.0,
            notes="To be paid off"
        )
    )
    
    assert item1.id is not None
    assert item2.id is not None
    
    # 2. Verify summary
    summary = service.get_summary(user_id=1)
    assert summary.total_assets == 50000.0
    assert summary.total_liabilities == 10000.0
    assert summary.net_worth == 40000.0
    assert len(summary.items) == 2
    
    # 3. Update an item
    updated = service.update_item(
        user_id=1,
        item_id=item2.id,
        payload=NetWorthItemUpdate(amount=5000.0)
    )
    assert updated.amount == 5000.0
    
    summary2 = service.get_summary(user_id=1)
    assert summary2.net_worth == 45000.0
    
    # 4. Take snapshot
    snapshot = service.take_snapshot(user_id=1)
    assert snapshot.net_worth == 45000.0
    assert snapshot.snapshot_date == date.today()
    
    # 5. Delete item (soft delete)
    success = service.delete_item(user_id=1, item_id=item1.id)
    assert success is True
    
    summary3 = service.get_summary(user_id=1)
    assert len(summary3.items) == 1
    assert summary3.total_assets == 0.0
    assert summary3.net_worth == -5000.0
