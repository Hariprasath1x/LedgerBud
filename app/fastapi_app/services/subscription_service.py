"""Subscription service — detection, CRUD, confirmation."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.fastapi_app.models.subscription import Subscription
from app.fastapi_app.models.transaction import Transaction
from app.fastapi_app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate


class SubscriptionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_subscriptions(self, user_id: int, confirmed_only: bool = False) -> list[Subscription]:
        stmt = select(Subscription).where(Subscription.user_id == user_id, Subscription.is_active == True)
        if confirmed_only:
            stmt = stmt.where(Subscription.is_confirmed == True)
        return list(self.session.scalars(stmt.order_by(Subscription.amount.desc())).all())

    def get_subscription(self, user_id: int, sub_id: int) -> Subscription | None:
        return self.session.scalar(
            select(Subscription).where(Subscription.id == sub_id, Subscription.user_id == user_id)
        )

    def create_subscription(self, user_id: int, payload: SubscriptionCreate) -> Subscription:
        sub = Subscription(
            user_id=user_id,
            name=payload.name,
            merchant_name=payload.merchant_name,
            amount=payload.amount,
            frequency=payload.frequency,
            category=payload.category,
            last_detected=payload.last_detected,
            next_expected=payload.next_expected,
            detection_confidence=payload.detection_confidence,
            is_confirmed=False,
        )
        self.session.add(sub)
        self.session.commit()
        self.session.refresh(sub)
        return sub

    def update_subscription(self, user_id: int, sub_id: int, payload: SubscriptionUpdate) -> Subscription | None:
        sub = self.get_subscription(user_id, sub_id)
        if not sub:
            return None
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(sub, field, value)
        self.session.commit()
        self.session.refresh(sub)
        return sub

    def confirm_subscription(self, user_id: int, sub_id: int) -> Subscription | None:
        sub = self.get_subscription(user_id, sub_id)
        if not sub:
            return None
        sub.is_confirmed = True
        self.session.commit()
        self.session.refresh(sub)
        return sub

    def dismiss_subscription(self, user_id: int, sub_id: int) -> bool:
        sub = self.get_subscription(user_id, sub_id)
        if not sub:
            return False
        sub.is_active = False
        self.session.commit()
        return True

    def detect_subscriptions(self, user_id: int) -> list[dict]:
        """
        Rule-based recurring payment detection from transactions.
        Groups transactions by merchant and identifies recurring patterns.
        """
        # Fetch all expense transactions for the user (last 6 months)
        cutoff = date.today() - timedelta(days=180)
        transactions = self.session.scalars(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "Expense",
                Transaction.transaction_date >= cutoff,
            )
        ).all()

        # Group by merchant name
        merchant_groups: dict[str, list[Transaction]] = defaultdict(list)
        for t in transactions:
            key = (t.merchant_name or "Unknown").strip().lower()
            merchant_groups[key].append(t)

        detected: list[dict] = []
        for merchant_key, txns in merchant_groups.items():
            if len(txns) < 2:
                continue

            # Check for consistent amounts
            amounts = [float(t.amount) for t in txns]
            unique_amounts = set(round(a, 0) for a in amounts)
            if len(unique_amounts) > 2:
                continue  # Too variable

            # Most common amount
            from collections import Counter
            amount_counter = Counter(round(a, 0) for a in amounts)
            most_common_amount = amount_counter.most_common(1)[0][0]
            confidence = amount_counter.most_common(1)[0][1] / len(txns)

            if confidence < 0.6:
                continue

            # Determine frequency from date gaps
            dates = sorted(t.transaction_date for t in txns)
            if len(dates) >= 2:
                gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
                avg_gap = sum(gaps) / len(gaps)
                if avg_gap < 10:
                    frequency = "weekly"
                elif avg_gap < 35:
                    frequency = "monthly"
                elif avg_gap < 100:
                    frequency = "quarterly"
                else:
                    frequency = "yearly"
            else:
                frequency = "monthly"

            last_date = max(dates)
            freq_days = {"weekly": 7, "monthly": 30, "quarterly": 90, "yearly": 365}
            next_exp = last_date + timedelta(days=freq_days.get(frequency, 30))

            detected.append({
                "name": txns[0].merchant_name,
                "merchant_name": txns[0].merchant_name,
                "amount": most_common_amount,
                "frequency": frequency,
                "last_detected": last_date,
                "next_expected": next_exp,
                "detection_confidence": round(confidence, 2),
                "category": txns[0].category,
                "transaction_count": len(txns),
            })

        return sorted(detected, key=lambda x: x["amount"], reverse=True)

    def sync_detected(self, user_id: int) -> int:
        """Persist newly detected subscriptions to the database, skipping existing ones."""
        detected = self.detect_subscriptions(user_id)
        existing_names = {
            s.name.lower()
            for s in self.session.scalars(
                select(Subscription).where(Subscription.user_id == user_id, Subscription.is_active == True)
            ).all()
        }

        new_count = 0
        for item in detected:
            name_key = (item["name"] or "").lower()
            if name_key in existing_names:
                continue
            sub = Subscription(
                user_id=user_id,
                name=item["name"] or "Unknown",
                merchant_name=item["merchant_name"],
                amount=item["amount"],
                frequency=item["frequency"],
                category=item["category"],
                last_detected=item["last_detected"],
                next_expected=item["next_expected"],
                detection_confidence=item["detection_confidence"],
                is_confirmed=False,
            )
            self.session.add(sub)
            new_count += 1

        if new_count > 0:
            self.session.commit()
        return new_count
