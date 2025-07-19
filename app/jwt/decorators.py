
from flask.globals import request
from flask.json import jsonify
from flask.globals import g
from functools import wraps

from app.jwt.utils import verify_token
from app.user.models import User

def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        authorization: str = request.headers.get('Authorization', None)
        
        if not authorization or not authorization.startswith('Bearer '):
            return jsonify({"error": "Authorization header missing or invalid"}), 401
            
        token: str = authorization.split()[1]
        payload: dict = verify_token(token)

        if not payload:
            return jsonify({"error": "Invalid token"}), 401
        
        if not User.query.filter_by(id=payload.get('user_id', None)).first():
            return jsonify({"error": "Invalid token"}), 401

        g.jwt_payload = payload.copy()

        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        payload: dict = g.jwt_payload
        user_role: str = payload.get('role', None)
        if not user_role:
            return jsonify({"error": "Invalid Token"}), 400
        
        if user_role != 'admin':
            return jsonify({'error', 'No Access'}), 403
        
        return fn(*args, **kwargs)
    return wrapper