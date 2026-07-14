"""Net worth service."""

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from datetime import date
from collections import defaultdict

from app.fastapi_app.models.net_worth import NetWorthItem, NetWorthSnapshot
from app.fastapi_app.schemas.net_worth import NetWorthItemCreate, NetWorthItemUpdate, NetWorthSummary, CategoryTotal


class NetWorthService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_items(self, user_id: int) -> list[NetWorthItem]:
        return list(
            self.session.scalars(
                select(NetWorthItem)
                .where(NetWorthItem.user_id == user_id, NetWorthItem.is_active == True)
                .order_by(NetWorthItem.item_type, NetWorthItem.amount.desc())
            ).all()
        )

    def get_item(self, user_id: int, item_id: int) -> NetWorthItem | None:
        return self.session.scalar(
            select(NetWorthItem).where(NetWorthItem.id == item_id, NetWorthItem.user_id == user_id, NetWorthItem.is_active == True)
        )

    def create_item(self, user_id: int, payload: NetWorthItemCreate) -> NetWorthItem:
        item = NetWorthItem(
            user_id=user_id,
            name=payload.name,
            item_type=payload.item_type,
            category=payload.category,
            amount=payload.amount,
            notes=payload.notes
        )
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def update_item(self, user_id: int, item_id: int, payload: NetWorthItemUpdate) -> NetWorthItem | None:
        item = self.get_item(user_id, item_id)
        if not item:
            return None
        
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(item, field, value)
            
        self.session.commit()
        self.session.refresh(item)
        return item

    def delete_item(self, user_id: int, item_id: int) -> bool:
        item = self.get_item(user_id, item_id)
        if not item:
            return False
        item.is_active = False
        self.session.commit()
        return True

    def get_summary(self, user_id: int) -> NetWorthSummary:
        items = self.list_items(user_id)
        
        total_assets = 0.0
        total_liabilities = 0.0
        
        asset_cats: dict[str, float] = defaultdict(float)
        liability_cats: dict[str, float] = defaultdict(float)
        
        for item in items:
            amount = float(item.amount)
            if item.item_type == "asset":
                total_assets += amount
                asset_cats[item.category] += amount
            else:
                total_liabilities += amount
                liability_cats[item.category] += amount
                
        asset_categories = [CategoryTotal(category=k, amount=v) for k, v in asset_cats.items()]
        liability_categories = [CategoryTotal(category=k, amount=v) for k, v in liability_cats.items()]
        
        # Sort by amount descending
        asset_categories.sort(key=lambda x: x.amount, reverse=True)
        liability_categories.sort(key=lambda x: x.amount, reverse=True)

        return NetWorthSummary(
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            net_worth=total_assets - total_liabilities,
            asset_categories=asset_categories,
            liability_categories=liability_categories,
            items=items
        )

    def take_snapshot(self, user_id: int) -> NetWorthSnapshot:
        summary = self.get_summary(user_id)
        
        snapshot = NetWorthSnapshot(
            user_id=user_id,
            snapshot_date=date.today(),
            total_assets=summary.total_assets,
            total_liabilities=summary.total_liabilities,
            net_worth=summary.net_worth
        )
        self.session.add(snapshot)
        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot

    def list_snapshots(self, user_id: int, limit: int = 30) -> list[NetWorthSnapshot]:
        return list(
            self.session.scalars(
                select(NetWorthSnapshot)
                .where(NetWorthSnapshot.user_id == user_id)
                .order_by(NetWorthSnapshot.snapshot_date.asc())
                .limit(limit)
            ).all()
        )
