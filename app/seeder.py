"""
Database Seeder
Seeds initial categories and merchant dictionary.
"""
import logging
from app.extensions import db
from app.models import Category, Merchant
from app.intelligence.merchant_dict import MERCHANT_SEED_DATA

logger = logging.getLogger(__name__)

CATEGORY_SEED_DATA = [
    # Expense categories
    ('Food & Dining', 'expense', '#ff6b6b', 'utensils'),
    ('Groceries', 'expense', '#ffa502', 'shopping-basket'),
    ('Shopping', 'expense', '#6c63ff', 'shopping-bag'),
    ('Entertainment', 'expense', '#ff4757', 'film'),
    ('Travel', 'expense', '#00d4a8', 'plane'),
    ('Utilities', 'expense', '#1e90ff', 'zap'),
    ('Healthcare', 'expense', '#2ed573', 'heart'),
    ('Education', 'expense', '#eccc68', 'book'),
    ('Investments', 'expense', '#a29bfe', 'trending-up'),
    ('Insurance', 'expense', '#74b9ff', 'shield'),
    ('Loan Repayment', 'expense', '#ff7675', 'credit-card'),
    ('Credit Card', 'expense', '#fd79a8', 'credit-card'),
    ('Cash Withdrawal', 'expense', '#636e72', 'dollar-sign'),
    ('Rent', 'expense', '#e17055', 'home'),
    ('Transfers', 'expense', '#0984e3', 'send'),
    ('Miscellaneous', 'expense', '#b2bec3', 'more-horizontal'),

    # Income categories
    ('Salary', 'income', '#00b894', 'briefcase'),
    ('Interest', 'income', '#00cec9', 'percent'),
    ('Rental Income', 'income', '#fdcb6e', 'home'),
    ('Refunds', 'income', '#6c5ce7', 'rotate-ccw'),
    ('Freelance', 'income', '#e84393', 'code'),
    ('Other Income', 'income', '#55efc4', 'plus-circle'),
]


def seed_categories():
    """Seed default categories if they don't exist."""
    count = 0
    for name, cat_type, color, icon in CATEGORY_SEED_DATA:
        existing = Category.query.filter_by(name=name).first()
        if not existing:
            cat = Category(name=name, type=cat_type, color=color, icon=icon, is_system=True)
            db.session.add(cat)
            count += 1

    db.session.commit()
    logger.info(f'Seeded {count} categories')
    return count


def seed_merchants():
    """Seed merchant dictionary from MERCHANT_SEED_DATA."""
    # Build category lookup
    categories = {c.name: c for c in Category.query.all()}
    count = 0

    for canonical_name, category_name, keywords in MERCHANT_SEED_DATA:
        existing = Merchant.query.filter_by(canonical_name=canonical_name).first()
        if not existing:
            category = categories.get(category_name)
            merchant = Merchant(
                name=canonical_name,
                canonical_name=canonical_name,
                category_id=category.id if category else None,
                keywords=keywords,
                is_verified=True,
            )
            db.session.add(merchant)
            count += 1

    db.session.commit()
    logger.info(f'Seeded {count} merchants')
    return count


def seed_all():
    """Run all seeders."""
    cat_count = seed_categories()
    mer_count = seed_merchants()
    logger.info(f'Database seeded: {cat_count} categories, {mer_count} merchants')
    return cat_count, mer_count
