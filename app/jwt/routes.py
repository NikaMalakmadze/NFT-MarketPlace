
from flask.helpers import redirect, url_for
from flask.globals import request
from flask.json import jsonify
from flask import Response

from app.jwt.utils import verify_token, generate_tokens
from config import settings
from app.jwt import jwt_bp

@jwt_bp.route('/public-key', methods=['GET'])
def get_public_key() -> Response:
    try:
        public_key: str = settings.jwt.PUBLIC_KEY.read_text()
        return jsonify({'status': 'success', 'key': public_key}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@jwt_bp.route('/refresh', methods=['POST'])
def refresh() -> Response:
    refresh_token: str = request.cookies.get('refresh_token')
    if not refresh_token:
        return jsonify({'error': 'Refresh token missing'}), 401
    
    payload: dict = verify_token(refresh_token, 'refresh')
    if not payload:
        response = jsonify({'error': 'Invalid Token'})
        response.set_cookie('refresh_token', '', expires=0, httponly=True, secure=True, samesite='Strict')
        return redirect(url_for('main.login'))
    
    user_id: int = payload.get('user_id')
    role: str = payload.get('role')
    new_access_token, new_refresh_token = generate_tokens(user_id, role)

    response: Response = jsonify({'access_token': new_access_token})

    response.set_cookie(
        'refresh_token',
        new_refresh_token,
        httponly=True,
        secure=True,
        samesite='Strict',
        max_age=settings.jwt.JWT_REFRESH_TOKEN_EXPIRES * 60
    )

    return response, 200