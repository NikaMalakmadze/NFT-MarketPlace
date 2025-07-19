
from flask.globals import request
from flask.json import jsonify
import os

from app.jwt.decorators import admin_required, jwt_required
from app.api.allowedwallets.schemas import AllowedwalletResponse, AllowedWalletCreate
from app.api.allowedwallets.models import AllowedWallet
from app.api.allowedwallets import allowed_wallets_bp
from app.api.utils import validate_values
from app.extensions import db

@allowed_wallets_bp.route('/', methods=['GET'])
@jwt_required
@admin_required
def get_allowed_wallets():
    wallets = AllowedWallet.query.all()
    if not wallets: 
        return jsonify({'status': 'Not Found', 'message': 'No allowed wallets'}), 404
    return jsonify([
        AllowedwalletResponse.model_validate(wallet, from_attributes=True).model_dump() for wallet in wallets
    ])

@allowed_wallets_bp.route('/add', methods=['POST'])
@jwt_required
@admin_required
def add_allowed_wallets():
    wallet_name = request.args.get('cardname')
    wallet_logo = request.args.get('cardlogo')
    validated_value = validate_values(
        {
            'name': wallet_name,
            'logo': wallet_logo
        },
        validator=AllowedWalletCreate,
        model=AllowedWallet,
        item_name='card',
        find_model_by='name'
    )
    if validated_value is tuple:
        return validated_value

    if validated_value:
        return jsonify({
            'status': 'exists',
            'message': f"Wallet '{validated_value.name}' is already allowed",
            'wallet_id': validated_value.id
        }), 200 
    
    new_allowed_wallet = AllowedWallet(name=wallet_name, logo=wallet_logo)
    db.session.add(new_allowed_wallet)
    db.session.commit()

    return jsonify({
            'status': 'succsess', 
            'message': f'{wallet_name} wallet was allowed',
            'walletInformation': AllowedwalletResponse.model_validate(new_allowed_wallet, from_attributes=True).model_dump()
         }), 201

@allowed_wallets_bp.route('/delete', methods=['DELETE'])
@jwt_required
@admin_required
def delete_allowed_wallet():
    validated_value = validate_values(
        {
            'name': request.args.get('cardname'),
            'logo': request.args.get('cardlogo')
        },
        validator=AllowedWalletCreate,
        model=AllowedWallet,
        item_name='card',
        find_model_by='name'
    )
    if not validated_value:
        return jsonify({'status': 'error', 'message': f'{validated_value.name} wallet was not found'}), 404
    
    if validated_value is tuple: 
        return validated_value

    if os.path.isfile(validated_value.logo):
        os.remove(validated_value.logo)

    db.session.delete(validated_value)
    db.session.commit()

    return jsonify({
        'status': 'succsess', 
        'message': f'{validated_value.name} is Forbidden from this moment',
        'walletInformation': AllowedwalletResponse.model_validate(validated_value, from_attributes=True).model_dump()
    }), 200
