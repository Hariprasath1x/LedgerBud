"""Net worth calculations for the finance dashboard."""

from typing import Dict, List

from app.models import Wallet


LIABILITY_TYPES = {'credit', 'credit_card', 'loan', 'liability'}


def get_net_worth_summary() -> Dict:
    wallets = Wallet.query.filter_by(is_active=True).all()

    assets: List[Dict] = []
    liabilities: List[Dict] = []

    for wallet in wallets:
        wallet_type = (wallet.type or '').lower()
        entry = {
            'id': wallet.id,
            'name': wallet.name,
            'type': wallet_type,
            'balance': float(wallet.balance or 0),
        }
        if wallet_type in LIABILITY_TYPES:
            liabilities.append(entry)
        else:
            assets.append(entry)

    total_assets = sum(item['balance'] for item in assets)
    total_liabilities = sum(item['balance'] for item in liabilities)
    net_worth = total_assets - total_liabilities

    return {
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'net_worth': net_worth,
        'assets': assets,
        'liabilities': liabilities,
        'asset_count': len(assets),
        'liability_count': len(liabilities),
    }
