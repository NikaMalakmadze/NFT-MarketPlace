
from app.api.allowedwallets.models import AllowedWallet

def validate_wallet_id(card_id: str) -> str:
    if not card_id:
        raise ValueError('Missing Wallet Id!')

    find_card = AllowedWallet.query.filter_by(id=card_id).first()
    if not find_card:
        raise ValueError('Invalid Wallet Id!')
    return find_card