
from flask.json import jsonify

from app.user.models import User

def validate_user_id(user_id: int) -> User | tuple:
    user: User = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'status': 'error', 'errors': ['No such User']}), 404
    return user